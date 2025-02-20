"""Client implementation for Azure OpenAI API integration.

This module provides a client for interacting with Azure OpenAI's API endpoints.
It supports:
- Multiple deployment configurations
- Streaming responses
- Automatic retries with exponential backoff
- Token usage tracking
- Proper error handling
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from openai import AsyncAzureOpenAI

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider

logger = logging.getLogger(__name__)


class AzureOpenAIClient(BaseProvider):
    """Client for Azure OpenAI API.

    This client provides access to Azure-hosted OpenAI models through their API endpoint.
    It supports:
    - Multiple deployment configurations
    - Streaming responses
    - Automatic retries with exponential backoff
    - Token usage tracking
    - Proper error handling
    """

    def __init__(
        self,
        azure_deployment: str,
        model: str,
        api_version: str,
        azure_endpoint: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        model_info: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Azure OpenAI client.

        Args:
            azure_deployment: Azure deployment name
            model: Model identifier
            api_version: Azure OpenAI API version
            azure_endpoint: Azure endpoint URL
            api_key: Optional API key (falls back to DefaultAzureCredential)
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            model_info: Model capabilities information
        """
        super().__init__()
        self.model_info = (
            BaseModelInfo(**model_info) if isinstance(model_info, dict) 
            else model_info or BaseModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                family="azure_openai"
            )
        )
        self.deployment = azure_deployment
        self.model = model
        self.api_version = api_version
        self.endpoint = azure_endpoint
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            max_retries=max_retries,
            timeout=timeout,
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Generate a completion for the given messages.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for generation

        Returns:
            Generated text completion
        """
        try:
            # Remove cancellation_token if present
            kwargs.pop('cancellation_token', None)

            # Prepare the request parameters
            request_params = {
                "messages": messages,
                "model": self.deployment,
                "max_completion_tokens": kwargs.get("max_completion_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": False
            }

            # Merge any additional parameters
            request_params.update({k: v for k, v in kwargs.items() if k not in ["max_completion_tokens", "temperature", "stream", "n", "logprobs", "echo", "stop", "presence_penalty", "frequency_penalty", "best_of", "logit_bias", "user"]})

            # Create the completion
            response = await self.client.create(**request_params)

            # Extract and return the text
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error creating completion: {e}")
            raise

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion for the given messages.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for generation

        Yields:
            Streaming text tokens
        """
        try:
            # Remove cancellation_token if present
            kwargs.pop('cancellation_token', None)

            # Prepare the request parameters
            request_params = {
                "messages": messages,
                "model": self.deployment,
                "max_completion_tokens": kwargs.get("max_completion_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": True
            }

            # Merge any additional parameters
            request_params.update({k: v for k, v in kwargs.items() if k not in ["max_completion_tokens", "temperature", "stream", "n", "logprobs", "echo", "stop", "presence_penalty", "frequency_penalty", "best_of", "logit_bias", "user"]})

            # Create the streaming completion
            async for chunk in await self.client.create(**request_params):
                # Extract the token from the chunk
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error creating streaming completion: {e}")
            raise

    async def create(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a chat completion.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional arguments to pass to the completion API

        Returns:
            The completion response
        """
        try:
            # Remove cancellation_token if present
            kwargs.pop('cancellation_token', None)

            # Convert message objects to dictionaries
            processed_messages = []
            for msg in messages:
                processed_msg = {
                    "role": getattr(msg, "role", "user"),
                    "content": msg.content
                }
                processed_messages.append(processed_msg)

            # Prepare the request parameters
            request_params = {
                "model": self.deployment,
                "messages": processed_messages,
                "max_completion_tokens": kwargs.get("max_completion_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": kwargs.get("stream", False)
            }

            # Merge any additional parameters
            request_params.update({k: v for k, v in kwargs.items() if k not in ["max_completion_tokens", "temperature", "stream", "n", "logprobs", "echo", "stop", "presence_penalty", "frequency_penalty", "best_of", "logit_bias", "user"]})

            # Create the completion
            response = await self.client.chat.completions.create(**request_params)

            return {
                "choices": [
                    {
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason,
                        "index": choice.index
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "completion_tokens": response.usage.completion_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error creating completion: {e}")
            raise

    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information as a dictionary.

        Returns:
            Dictionary representation of model capabilities
        """
        return {
            "vision": self.model_info.vision,
            "function_calling": self.model_info.function_calling,
            "json_output": self.model_info.json_output,
            "family": self.model_info.family
        }
