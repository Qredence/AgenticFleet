"""Google Gemini API client implementation.

This module provides a client for interacting with Google's Gemini models through
their API endpoint. It supports both text and multimodal inputs, with proper error
handling and async capabilities.
"""

import asyncio
import base64
import json
import logging
import os
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
from autogen_core.models import LLMMessage, UserMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Base exception for Gemini client errors."""

    pass


class GeminiModels(str, Enum):
    """Supported Gemini models."""

    GEMINI_FLASH_THINKING = "gemini-2.0-flash-thinking-exp-01-21"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_EXP = "gemini-exp-1206"

    @classmethod
    def get_model_capabilities(cls, model: str) -> Dict[str, bool]:
        """Get model capabilities based on model type.

        Args:
            model: Model identifier

        Returns:
            Dict of model capabilities
        """
        capabilities = {
            "function_calling": True,
            "json_output": True,
            "family": "gemini",
        }

        if "vision" in model.lower():
            capabilities.update(
                {
                    "vision": True,
                    "image_analysis": True,
                    "multimodal": True,
                }
            )
        else:
            capabilities["vision"] = False

        if "ultra" in model.lower():
            capabilities.update(
                {
                    "advanced_reasoning": True,
                    "complex_tasks": True,
                }
            )

        return capabilities


class GeminiClient(BaseProvider):
    """Client for Google Gemini API.

    This client provides access to Google's Gemini models through their API endpoint.
    It supports:
    - Multiple model variants (Pro, Vision, Ultra)
    - Multimodal inputs (text + images)
    - Streaming responses
    - Rate limiting and retry mechanisms
    - Token usage tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = GeminiModels.GEMINI_FLASH_THINKING.value,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        model_info: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit_rpm: int = 60,
    ):
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key. If not provided, will look for GEMINI_API_KEY env var.
            model: Model identifier
            base_url: Gemini API base URL
            model_info: Model capabilities information
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            rate_limit_rpm: Maximum requests per minute

        Raises:
            ValueError: If API key is not provided or model is not supported
            GeminiError: For other initialization errors
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. "
                "Either provide it directly or set GEMINI_API_KEY environment variable."
            )

        # Validate and set model
        try:
            self.model = GeminiModels(model).value
        except ValueError:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {', '.join(m.value for m in GeminiModels)}"
            )

        self.base_url = base_url.rstrip("/")
        self.model_info = model_info or GeminiModels.get_model_capabilities(model)
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
            "x-goog-api-key": self.api_key,
        }

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Format messages for the API."""
        formatted = []
        for msg in messages:
            content = []

            # Handle text content
            if isinstance(msg.content, str):
                content.append({"type": "text", "text": msg.content})
            # Handle multimodal content (assuming base64 encoded images)
            elif isinstance(msg.content, dict) and "image" in msg.content:
                content.extend(
                    [
                        {"type": "text", "text": msg.content.get("text", "")},
                        {
                            "type": "image",
                            "image": {
                                "mime_type": msg.content["image"].get("mime_type", "image/jpeg"),
                                "data": msg.content["image"]["data"],
                            },
                        },
                    ]
                )

            formatted.append(
                {"role": "user" if isinstance(msg, UserMessage) else "model", "parts": content}
            )
        return formatted

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True
    )
    async def generate(
        self,
        prompt: Union[str, List[LLMMessage], Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response from the model.

        Args:
            prompt: Input prompt, list of messages, or dict with text/image
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API call

        Returns:
            Generated response text

        Raises:
            GeminiError: For API-related errors
            Exception: For other errors
        """
        await self._check_rate_limit()

        # Handle different input types
        if isinstance(prompt, str):
            messages = [{"role": "user", "parts": [{"type": "text", "text": prompt}]}]
        elif isinstance(prompt, dict):
            messages = [{"role": "user", "parts": self._format_content(prompt)}]
        else:
            messages = self._format_messages(prompt)

        data = {
            "contents": messages,
            "generationConfig": {
                "temperature": temperature,
                "candidateCount": 1,
                **kwargs,
            },
        }

        if max_tokens:
            data["generationConfig"]["maxOutputTokens"] = max_tokens

        try:
            async with aiohttp.ClientSession(
                headers=self._get_headers(), timeout=self.timeout
            ) as session:
                url = f"{self.base_url}/models/{self.model}:generateContent"
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise GeminiError(f"Gemini API error: {error_text}")

                    result = await response.json()

                    # Update token usage if available
                    usage = result.get("usageMetadata", {})
                    self.total_prompt_tokens += usage.get("promptTokenCount", 0)
                    self.total_completion_tokens += usage.get("candidatesTokenCount", 0)

                    return result["candidates"][0]["content"]["parts"][0]["text"]

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Gemini API: {e}")
            raise GeminiError(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Error during Gemini API call: {e}")
            raise

    async def stream(
        self,
        prompt: Union[str, List[LLMMessage], Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream responses from the model.

        Args:
            prompt: Input prompt, list of messages, or dict with text/image
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional parameters for the API call

        Yields:
            Generated response text chunks

        Raises:
            GeminiError: For API-related errors
            Exception: For other errors
        """
        await self._check_rate_limit()

        # Handle different input types
        if isinstance(prompt, str):
            messages = [{"role": "user", "parts": [{"type": "text", "text": prompt}]}]
        elif isinstance(prompt, dict):
            messages = [{"role": "user", "parts": self._format_content(prompt)}]
        else:
            messages = self._format_messages(prompt)

        data = {
            "contents": messages,
            "generationConfig": {
                "temperature": temperature,
                "candidateCount": 1,
                **kwargs,
            },
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession(
                headers=self._get_headers(), timeout=self.timeout
            ) as session:
                url = f"{self.base_url}/models/{self.model}:streamGenerateContent"
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise GeminiError(f"Gemini API error: {error_text}")

                    async for line in response.content:
                        if line:
                            try:
                                result = json.loads(line)
                                if "candidates" in result:
                                    text = result["candidates"][0]["content"]["parts"][0].get(
                                        "text", ""
                                    )
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse streaming response: {line}")

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Gemini API: {e}")
            raise GeminiError(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Error during Gemini API streaming: {e}")
            raise

    def _format_content(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format mixed content (text/image) for the API."""
        parts = []

        # Add text content if present
        if "text" in content:
            parts.append({"type": "text", "text": content["text"]})

        # Add image content if present
        if "image" in content:
            image_data = content["image"]
            if isinstance(image_data, str):
                # Assume base64 encoded image
                parts.append(
                    {
                        "type": "image",
                        "image": {
                            "mime_type": "image/jpeg",  # Default to JPEG
                            "data": image_data,
                        },
                    }
                )
            elif isinstance(image_data, dict):
                # Assume properly formatted image data
                parts.append(
                    {
                        "type": "image",
                        "image": image_data,
                    }
                )

        return parts

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


__all__ = ["GeminiClient"]
