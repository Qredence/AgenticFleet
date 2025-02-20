"""Client implementation for OpenAI API integration.

This module provides a client for interacting with OpenAI's API endpoints.
It supports both streaming and non-streaming responses, with proper error
handling and async capabilities.
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from autogen_ext.models.openai import OpenAIChatCompletionClient as ExtOpenAIClient

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider

logger = logging.getLogger(__name__)


class OpenAIClient(BaseProvider):
    """Client for interacting with OpenAI API.

    This client provides access to OpenAI's API endpoints.
    It supports:
    - Multiple model variants
    - Streaming responses
    - Custom model parameters
    - Proper error handling
    - Async operations
    """

    def __init__(
        self,
        model: str = "gpt-4-0125-preview",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model_info: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the OpenAI client.

        Args:
            model: The model to use for chat completions
            api_key: Optional API key. If not provided, will look for OPENAI_API_KEY env var
            temperature: Temperature for response generation (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            model_info: Optional model information dictionary
        """
        super().__init__()
        self.model_info = model_info or BaseModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            family="openai"
        )
        self.client = ExtOpenAIClient(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Generate a completion for the given messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional arguments to pass to the completion API

        Returns:
            The generated completion text
        """
        return await self.client.generate(messages, **kwargs)

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion for the given messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional arguments to pass to the completion API

        Yields:
            Generated completion text chunks
        """
        async for chunk in self.client.stream(messages, **kwargs):
            yield chunk

openai_model_client = OpenAIClient(
    model="gpt-4o-2024-08-06",
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY environment variable set.
)
