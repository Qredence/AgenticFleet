"""Factory module for creating model clients.

This module provides a factory pattern implementation for creating various LLM clients.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional, Type

from .base import BaseModelInfo
from .providers import (
    AzureAIFoundryClient,
    AzureOpenAIClient,
    DeepSeekClient,
    GeminiClient,
    OpenAIClient,
)


class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = auto()
    AZURE_OPENAI = auto()
    GEMINI = auto()
    DEEPSEEK = auto()
    AZURE_AI_FOUNDRY = auto()


class ModelFactory:
    """Factory class for creating model clients."""

    _provider_map: Dict[ModelProvider, Type[BaseModelInfo]] = {
        ModelProvider.OPENAI: OpenAIClient,
        ModelProvider.AZURE_OPENAI: AzureOpenAIClient,
        ModelProvider.GEMINI: GeminiClient,
        ModelProvider.DEEPSEEK: DeepSeekClient,
        ModelProvider.AZURE_AI_FOUNDRY: AzureAIFoundryClient,
    }

    @classmethod
    def create(cls, provider: ModelProvider, **kwargs: Any) -> BaseModelInfo:
        """Create a model client for the specified provider.

        Args:
            provider: The model provider to use
            **kwargs: Provider-specific configuration options

        Returns:
            A configured model client instance

        Raises:
            ValueError: If the provider is not supported
        """
        if provider not in cls._provider_map:
            raise ValueError(f"Unsupported provider: {provider}")

        client_class = cls._provider_map[provider]
        return client_class(**kwargs)

    @classmethod
    def create_default(cls, **kwargs: Any) -> BaseModelInfo:
        """Create the default model client (Azure OpenAI).

        Args:
            **kwargs: Provider-specific configuration options

        Returns:
            A configured Azure OpenAI client instance
        """
        return cls.create(ModelProvider.AZURE_OPENAI, **kwargs)
