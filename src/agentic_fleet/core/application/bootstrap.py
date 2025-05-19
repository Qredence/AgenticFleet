"""Core application bootstrap module."""

import os
from pathlib import Path
from typing import Any

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv

from agentic_fleet.config import config_manager
from agentic_fleet.core.application.manager import ApplicationConfig, ApplicationManager


def initialize_app() -> ApplicationManager:
    """Initialize the core application components.

    Returns:
        ApplicationManager: Initialized application manager
    """
    # Load environment variables
    load_dotenv()

    # Initialize configuration
    config_manager.load_all()
    app_settings = config_manager.get_app_settings()

    # Create application config
    config = ApplicationConfig(
        project_root=Path(os.getcwd()),
        config_path=Path("config"),
        debug=app_settings.get("debug", False),
        log_level=app_settings.get("log_level", "INFO"),
    )

    # Initialize application manager
    return ApplicationManager(config=config)


def _create_model_client(
    settings: dict[str, Any],
) -> AzureOpenAIChatCompletionClient | None:
    """Create Azure OpenAI model client from settings.

    Args:
        settings: Application settings dictionary

    Returns:
        Optional[AzureOpenAIChatCompletionClient]: Configured model client or None
    """
    try:
        return AzureOpenAIChatCompletionClient(
            api_key=settings.get("azure_openai_api_key"),
            api_version=settings.get("azure_openai_api_version"),
            azure_endpoint=settings.get("azure_openai_endpoint"),
            azure_deployment=settings.get("azure_openai_deployment"),
            model=settings.get("azure_openai_model"),
        )
    except Exception:
        return None
