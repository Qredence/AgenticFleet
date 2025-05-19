"""
DSPy Compiler Configuration for Azure OpenAI Mini Models.

This module provides a specialized DSPy compiler configuration tailored for
Azure OpenAI's o3-mini and gpt-4o-mini models, ensuring optimal performance
within their constraints.
"""

from datetime import datetime
from typing import Literal

import dspy
from dspy.teleprompt import PromptConfig


class AzureMiniCompiler(dspy.Compiler):
    """DSPy compiler configured specifically for Azure OpenAI mini models."""

    SUPPORTED_MODELS = Literal["o3-mini", "gpt-4o-mini"]
    DEFAULT_API_VERSION = "2024-12-01-preview"

    def __init__(
        self,
        model_name: SUPPORTED_MODELS,
        api_key: str,
        api_version: str = DEFAULT_API_VERSION,
        deployment: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ):
        """
        Initialize the Azure Mini Compiler.

        Args:
            model_name: The name of the Azure OpenAI model to use (o3-mini or gpt-4o-mini)
            api_key: Azure OpenAI API key
            api_version: API version to use (defaults to 2024-12-01-preview)
            deployment: Optional deployment name (defaults to model_name)
            base_url: Optional base URL for Azure OpenAI endpoint
            **kwargs: Additional configuration parameters
        """
        super().__init__()

        self.model_name = model_name
        self.api_version = api_version
        self.deployment = deployment or model_name

        # Configure for smaller context windows and optimized prompts
        self.config = PromptConfig(
            max_tokens=4096,  # Adjusted for mini models
            temperature=kwargs.get("temperature", 0.7),
            model=f"{model_name}-{self._get_model_date()}",
            azure_deployment=self.deployment,
            azure_endpoint=base_url,
            azure_api_version=api_version,
            azure_api_key=api_key,
        )

    def _get_model_date(self) -> str:
        """Get the current model version date."""
        current_date = datetime.now()
        return current_date.strftime("%Y-%m-%d")

    def compile(self, program: dspy.Program, temperature: float = 0.7, **kwargs) -> dspy.Prediction:
        """
        Compile a DSPy program with Azure mini model constraints.

        Args:
            program: The DSPy program to compile
            temperature: Temperature for generation (default: 0.7)
            **kwargs: Additional compilation parameters

        Returns:
            A compiled DSPy prediction
        """
        # Adjust configuration for specific compilation
        config = self.config.copy()
        config.temperature = temperature

        # Add any additional Azure-specific parameters
        azure_params = {k: v for k, v in kwargs.items() if k.startswith("azure_")}
        if azure_params:
            config.update(azure_params)

        return super().compile(program, config=config)

    def get_config(self) -> dict:
        """Get the current compiler configuration."""
        return {
            "model_name": self.model_name,
            "api_version": self.api_version,
            "deployment": self.deployment,
            "config": self.config.dict(),
        }
