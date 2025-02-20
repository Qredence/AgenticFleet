"""DeepSeek API client implementation.

This module provides a client for interacting with DeepSeek's models through their
OpenAI-compatible API endpoint. It supports multiple specialized models, function
calling, and automatic message formatting.
"""

import asyncio
import json
import logging
import os
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from autogen_core.models import LLMMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from tenacity import retry, stop_after_attempt, wait_exponential

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider

logger = logging.getLogger(__name__)

class DeepSeekError(Exception):
    """Base exception for DeepSeek client errors."""
    pass

class DeepSeekModels(str, Enum):
    """Supported DeepSeek models."""
    CHAT = "deepseek-chat"
    CODE = "deepseek-code"
    RESEARCH = "deepseek-reasoning"

    @classmethod
    def get_model_capabilities(cls, model: str) -> Dict[str, bool]:
        """Get model capabilities based on model type.
        
        Args:
            model: Model identifier
            
        Returns:
            Dict of model capabilities
        """
        capabilities = {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "deepseek",
        }
        
        if model == cls.CODE.value:
            capabilities.update({
                "code_completion": True,
                "code_generation": True,
                "code_explanation": True,
            })
        elif model == cls.RESEARCH.value:
            capabilities.update({
                "research_analysis": True,
                "citation_support": True,
                "literature_review": True,
            })
            
        return capabilities

class DeepSeekClient(BaseProvider):
    """DeepSeek client using OpenAI-compatible API.

    This client provides access to DeepSeek's models through their OpenAI-compatible
    API endpoint. It supports:
    - Multiple specialized models (chat, code, research)
    - Function calling capabilities
    - JSON output formatting
    - Automatic message formatting
    - Rate limiting and retry mechanisms
    - Token usage tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DeepSeekModels.CHAT.value,
        base_url: str = "https://api.deepseek.com/v1",
        model_info: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit_rpm: int = 60,
    ):
        """Initialize DeepSeek client.

        Args:
            api_key: DeepSeek API key. If not provided, will look for DEEPSEEK_API_KEY env var.
            model: Model identifier (e.g., "deepseek-chat", "deepseek-code")
            base_url: DeepSeek API base URL
            model_info: Model capabilities information
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            rate_limit_rpm: Maximum requests per minute

        Raises:
            ValueError: If API key is not provided or model is not supported
            DeepSeekError: For other initialization errors
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key is required. "
                "Either provide it directly or set DEEPSEEK_API_KEY environment variable."
            )

        # Validate and set model
        try:
            self.model = DeepSeekModels(model).value
        except ValueError:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {', '.join(m.value for m in DeepSeekModels)}"
            )

        self.base_url = base_url.rstrip("/")
        self.model_info = model_info or DeepSeekModels.get_model_capabilities(model)
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_rpm = rate_limit_rpm
        
        # Rate limiting state
        self._request_times = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Token usage tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            current_time = asyncio.get_event_loop().time()
            minute_ago = current_time - 60
            
            # Remove requests older than 1 minute
            self._request_times = [t for t in self._request_times if t > minute_ago]
            
            if len(self._request_times) >= self.rate_limit_rpm:
                sleep_time = 60 - (current_time - self._request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                    await asyncio.sleep(sleep_time)
            
            self._request_times.append(current_time)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Format messages for the API."""
        formatted = []
        for msg in messages:
            role = "user" if isinstance(msg, UserMessage) else "assistant"
            formatted.append({"role": role, "content": msg.content})
        return formatted

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate(
        self, 
        prompt: Union[str, List[LLMMessage]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate a response from the model.
        
        Args:
            prompt: Input prompt or list of messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated response text
            
        Raises:
            DeepSeekError: For API-related errors
            Exception: For other errors
        """
        await self._check_rate_limit()

        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = self._format_messages(prompt)

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
            **kwargs,
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens

        try:
            async with aiohttp.ClientSession(headers=self._get_headers(), timeout=self.timeout) as session:
                async with session.post(f"{self.base_url}/chat/completions", json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise DeepSeekError(f"DeepSeek API error: {error_text}")
                    
                    result = await response.json()
                    
                    # Update token usage
                    usage = result.get("usage", {})
                    self.total_prompt_tokens += usage.get("prompt_tokens", 0)
                    self.total_completion_tokens += usage.get("completion_tokens", 0)
                    
                    return result["choices"][0]["message"]["content"]
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to DeepSeek API: {e}")
            raise DeepSeekError(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Error during DeepSeek API call: {e}")
            raise

    async def stream(
        self, 
        prompt: Union[str, List[LLMMessage]], 
        temperature: float = 0.7,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream responses from the model.
        
        Args:
            prompt: Input prompt or list of messages
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional parameters for the API call
            
        Yields:
            Generated response text chunks
            
        Raises:
            DeepSeekError: For API-related errors
            Exception: For other errors
        """
        await self._check_rate_limit()

        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = self._format_messages(prompt)

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }

        try:
            async with aiohttp.ClientSession(headers=self._get_headers(), timeout=self.timeout) as session:
                async with session.post(f"{self.base_url}/chat/completions", json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise DeepSeekError(f"DeepSeek API error: {error_text}")
                    
                    async for line in response.content:
                        if line:
                            try:
                                if line.startswith(b"data: "):
                                    line = line[6:]  # Remove "data: " prefix
                                result = json.loads(line)
                                if result.get("choices"):
                                    content = result["choices"][0].get("delta", {}).get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse streaming response: {line}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to DeepSeek API: {e}")
            raise DeepSeekError(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Error during DeepSeek API streaming: {e}")
            raise

    def get_token_usage(self) -> Dict[str, int]:
        """Get current token usage statistics.
        
        Returns:
            Dict containing prompt and completion token counts
        """
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
        }
