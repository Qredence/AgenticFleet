"""CogCache API client implementation.

This module provides a client for interacting with CogCache's proxy API, which offers
caching and optimization for various LLM models. It supports caching, token usage tracking,
and metadata about cache performance.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from autogen_core.models import LLMMessage, UserMessage
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider

logger = logging.getLogger(__name__)


class CogCacheError(Exception):
    """Base exception for CogCache client errors."""
    pass


class CogCacheModels(str, Enum):
    """Supported CogCache models."""
    GPT4O = "gpt-4o-2024-08-06"
    GPT4O_MINI = "gpt-4o-mini-2024-07-18"

    @classmethod
    def get_model_capabilities(cls, model: str) -> Dict[str, Any]:
        """Get model capabilities based on model type.
        
        Args:
            model: Model identifier
            
        Returns:
            Dict of model capabilities
        """
        capabilities = {
            "function_calling": True,
            "json_output": True,
            "vision": False,
            "family": "cogcache",
        }
        
        if model == cls.GPT4O_MINI.value:
            capabilities.update({
                "fast_response": True,
                "cost_effective": True,
            })
        else:
            capabilities.update({
                "complex_reasoning": True,
                "planning": True,
            })
        
        return capabilities


@dataclass
class CacheMetadata:
    """Metadata about cache performance and behavior."""
    cache_hit: bool = False
    cache_ttl: Optional[int] = None
    cache_key: Optional[str] = None
    cache_size: Optional[int] = None
    cache_type: Optional[str] = None


class CogCacheResponse(BaseModel):
    """Response from CogCache API with caching metadata."""
    raw_response: Any
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            'cache_hit': False,
            'cache_ttl': None,
            'cache_key': None,
            'cache_size': None,
            'cache_type': None,
        }
    )


class CogCacheClient(BaseProvider):
    """Client for CogCache API with caching capabilities.
    
    This client provides access to CogCache's proxy API, which offers caching and
    optimization for various LLM models. It supports:
    - GPT-4o and GPT-4o mini models
    - Response caching
    - Cache performance tracking
    - Rate limiting and retry mechanisms
    - Token usage tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = CogCacheModels.GPT4O.value,
        base_url: str = "https://proxy-api.cogcache.com/v1",
        model_info: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit_rpm: int = 60,
        cache_ttl: Optional[int] = None,
    ):
        """Initialize CogCache client.
        
        Args:
            api_key: CogCache API key. If not provided, will look for COGCACHE_API_KEY env var.
            model: Model identifier
            base_url: CogCache API base URL
            model_info: Model capabilities information
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            rate_limit_rpm: Maximum requests per minute
            cache_ttl: Default cache TTL in seconds
            
        Raises:
            ValueError: If API key is not provided or model is not supported
            CogCacheError: For other initialization errors
        """
        self.api_key = api_key or os.getenv("COGCACHE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CogCache API key is required. "
                "Either provide it directly or set COGCACHE_API_KEY environment variable."
            )

        # Validate and set model
        try:
            self.model = CogCacheModels(model).value
        except ValueError:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {', '.join(m.value for m in CogCacheModels)}"
            )

        self.base_url = base_url.rstrip("/")
        self.model_info = model_info or CogCacheModels.get_model_capabilities(model)
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_rpm = rate_limit_rpm
        self.cache_ttl = cache_ttl
        
        # Rate limiting state
        self._request_times = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Usage tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cache_hits = 0
        self.total_cache_misses = 0

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication.
        
        Returns:
            Dict of headers including Authorization
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = asyncio.get_event_loop().time()
            minute_ago = now - 60
            
            # Remove old requests
            self._request_times = [t for t in self._request_times if t > minute_ago]
            
            if len(self._request_times) >= self.rate_limit_rpm:
                sleep_time = 60 - (now - self._request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            self._request_times.append(now)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: Union[str, List[LLMMessage]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        cache_ttl: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate a response from the model.
        
        Args:
            prompt: Input prompt or list of messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            cache_ttl: Cache TTL in seconds (overrides default)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated response text
            
        Raises:
            CogCacheError: For API-related errors
            Exception: For other errors
        """
        await self._check_rate_limit()
        
        messages = [UserMessage(content=prompt)] if isinstance(prompt, str) else prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": self.model,
                    "messages": [m.to_dict() for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "cache_ttl": cache_ttl or self.cache_ttl,
                    **kwargs
                },
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    raise CogCacheError(
                        f"Error from CogCache API: {response.status} - {await response.text()}"
                    )
                
                data = await response.json()
                
                # Update usage tracking
                if usage := data.get("usage"):
                    self.total_prompt_tokens += usage.get("prompt_tokens", 0)
                    self.total_completion_tokens += usage.get("completion_tokens", 0)
                
                # Update cache tracking
                cache_hit = "x-cache-hit" in response.headers
                if cache_hit:
                    self.total_cache_hits += 1
                else:
                    self.total_cache_misses += 1
                
                return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        prompt: Union[str, List[LLMMessage]],
        temperature: float = 0.7,
        cache_ttl: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream responses from the model.
        
        Args:
            prompt: Input prompt or list of messages
            temperature: Sampling temperature (0.0 to 1.0)
            cache_ttl: Cache TTL in seconds (overrides default)
            **kwargs: Additional parameters for the API call
            
        Yields:
            Generated response text chunks
            
        Raises:
            CogCacheError: For API-related errors
            Exception: For other errors
        """
        await self._check_rate_limit()
        
        messages = [UserMessage(content=prompt)] if isinstance(prompt, str) else prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json={
                    "model": self.model,
                    "messages": [m.to_dict() for m in messages],
                    "temperature": temperature,
                    "stream": True,
                    "cache_ttl": cache_ttl or self.cache_ttl,
                    **kwargs
                },
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    raise CogCacheError(
                        f"Error from CogCache API: {response.status} - {await response.text()}"
                    )
                
                # Update cache tracking
                cache_hit = "x-cache-hit" in response.headers
                if cache_hit:
                    self.total_cache_hits += 1
                else:
                    self.total_cache_misses += 1
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8').strip('data: '))
                            if content := data["choices"][0]["delta"].get("content"):
                                yield content
                        except Exception as e:
                            logger.warning(f"Error parsing streaming response: {e}")
                            continue

    def get_usage_stats(self) -> Dict[str, int]:
        """Get current usage statistics.
        
        Returns:
            Dict containing token usage and cache performance metrics
        """
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "cache_hits": self.total_cache_hits,
            "cache_misses": self.total_cache_misses,
            "cache_hit_rate": (
                self.total_cache_hits / (self.total_cache_hits + self.total_cache_misses)
                if self.total_cache_hits + self.total_cache_misses > 0
                else 0
            ),
        }
