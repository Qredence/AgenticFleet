"""Azure AI Foundry client implementation.

This module provides a client for interacting with Azure AI Foundry's models,
including Phi-4 and Llama-3.3-70b. It supports model deployment management,
token usage tracking, and response streaming.
"""

import os
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from autogen_core.models import LLMMessage, UserMessage
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider


class AzureAIFoundryModels(str, Enum):
    """Supported Azure AI Foundry models."""

    PHI4 = "phi-4"
    LLAMA70B = "llama-3.3-70b"

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
            "family": "azure_ai_foundry",
        }

        if model == cls.PHI4.value:
            capabilities.update(
                {
                    "code_generation": True,
                    "analysis": True,
                }
            )
        elif model == cls.LLAMA70B.value:
            capabilities.update(
                {
                    "complex_reasoning": True,
                    "research": True,
                }
            )

        return capabilities


class AzureAIFoundryClient(BaseProvider):
    """Client for Azure AI Foundry models.

    Features:
    - Support for Phi-4 and Llama-3.3-70b models
    - Token usage tracking
    - Response streaming
    - Automatic model capability detection
    """

    def __init__(
        self,
        deployment: str,
        model: str = AzureAIFoundryModels.PHI4.value,
        endpoint: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        api_key: Optional[str] = None,
        model_info: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Azure AI Foundry client.

        Args:
            deployment: Model deployment name
            model: Model identifier
            endpoint: API endpoint. If not provided, uses AZURE_AI_FOUNDRY_ENDPOINT env var
            api_version: API version to use
            api_key: API key. If not provided, uses AZURE_AI_FOUNDRY_API_KEY env var
            model_info: Model capabilities information
            **kwargs: Additional client configuration

        Raises:
            ValueError: If required parameters are missing
        """
        self.deployment = deployment
        self.endpoint = endpoint or os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        if not self.endpoint:
            raise ValueError(
                "Azure AI Foundry endpoint is required. "
                "Either provide it directly or set AZURE_AI_FOUNDRY_ENDPOINT environment variable."
            )

        self.api_key = api_key or os.getenv("AZURE_AI_FOUNDRY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Azure AI Foundry API key is required. "
                "Either provide it directly or set AZURE_AI_FOUNDRY_API_KEY environment variable."
            )

        # Validate and set model
        try:
            self.model = AzureAIFoundryModels(model).value
        except ValueError:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {', '.join(m.value for m in AzureAIFoundryModels)}"
            )

        self.api_version = api_version
        self.model_info = model_info or AzureAIFoundryModels.get_model_capabilities(model)

        # Initialize Azure client
        self.client = AzureAIChatCompletionClient(
            deployment=deployment,
            model=model,
            endpoint=self.endpoint,
            api_version=self.api_version,
            credential=AzureKeyCredential(self.api_key),
            model_info=self.model_info,
            **kwargs,
        )

        # Usage tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    async def generate(self, prompt: Union[str, List[LLMMessage]], **kwargs: Any) -> str:
        """Generate a response from the model.

        Args:
            prompt: Input prompt or list of messages
            **kwargs: Additional parameters for the API call

        Returns:
            Generated response text

        Raises:
            Exception: For API or generation errors
        """
        messages = [UserMessage(content=prompt)] if isinstance(prompt, str) else prompt
        response = await self.client.create(messages, **kwargs)

        # Update usage tracking
        if usage := getattr(response, "usage", None):
            self.total_prompt_tokens += usage.get("prompt_tokens", 0)
            self.total_completion_tokens += usage.get("completion_tokens", 0)

        return response.content

    async def stream(
        self, prompt: Union[str, List[LLMMessage]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream responses from the model.

        Args:
            prompt: Input prompt or list of messages
            **kwargs: Additional parameters for the API call

        Yields:
            Generated response text chunks
        """
        messages = [UserMessage(content=prompt)] if isinstance(prompt, str) else prompt
        async for chunk in self.client.stream(messages, **kwargs):
            if chunk.content:
                yield chunk.content

    def get_usage_stats(self) -> Dict[str, int]:
        """Get current token usage statistics.

        Returns:
            Dict containing prompt and completion token counts
        """
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
        }


__all__ = ["AzureAIFoundryClient"]
