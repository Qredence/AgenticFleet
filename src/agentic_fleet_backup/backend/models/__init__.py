"""AgenticFleet model implementations.

This module provides a unified interface for working with various LLM providers
through a factory pattern. Supported providers include:

- OpenAI
- Azure OpenAI
- Google Gemini
- Ollama (local models)
- DeepSeek
- Azure AI Foundry

Example usage:

    from agentic_fleet.models import ModelFactory, ModelProvider

    # Create an Azure OpenAI client
    azure_client = ModelFactory.create(
        ModelProvider.AZURE_OPENAI,
        deployment="your-deployment",
        model="gpt-4",
        endpoint="your-endpoint"
    )

    # Create a Gemini client
    gemini_client = ModelFactory.create(
        ModelProvider.GEMINI,
        api_key="your-api-key"
    )

    # Use the default client (Azure OpenAI)
    default_client = ModelFactory.create_default()
"""

from .base import BaseModelInfo
from .factory import ModelFactory, ModelProvider
from .providers import (
    AzureAIFoundryClient,
    AzureOpenAIClient,
    DeepSeekClient,
    GeminiClient,
    OpenAIClient,
)

__all__ = [
    'ModelFactory',
    'ModelProvider',
    'BaseModelInfo',
    'OpenAIClient',
    'AzureOpenAIClient',
    'GeminiClient',
    'DeepSeekClient',
    'AzureAIFoundryClient',
]
