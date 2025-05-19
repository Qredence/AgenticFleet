"""Module for handling UI settings and chat profiles."""

# Standard library imports
import logging
from typing import Any

# Third-party imports
import chainlit as cl
from chainlit.input_widget import Select, Slider, Switch

# Local imports
from agentic_fleet.config import config_manager

# Initialize logging
logger = logging.getLogger(__name__)


class SettingsManager:
    """Class for managing chat settings and profiles."""

    def __init__(self) -> None:
        """Initialize the settings manager."""
        self.defaults = config_manager.get_defaults()

    def get_default_settings(self) -> dict[str, Any]:
        """Get default settings values.

        Returns:
            Dictionary of default settings
        """
        # Handle DefaultsConfig object which doesn't have a get method
        defaults_dict = self.defaults.__dict__ if hasattr(self.defaults, "__dict__") else {}

        return {
            "max_rounds": defaults_dict.get("max_rounds", 10),
            "max_time": defaults_dict.get("max_time", 300),
            "max_stalls": defaults_dict.get("max_stalls", 3),
            "start_page": defaults_dict.get("start_page", "https://www.bing.com"),
            "temperature": defaults_dict.get("temperature", 0.7),
            "system_prompt": defaults_dict.get("system_prompt", ""),
        }

    async def setup_chat_settings(self) -> None:
        """Initialize chat settings with default values and UI elements."""
        # Get default settings
        defaults = self.get_default_settings()

        # Register chat settings
        await cl.ChatSettings(
            [
                Select(
                    id="model",
                    label="Model",
                    values=["gpt-4.1-nano", "gpt-4.1-mini"],
                    initial_value="gpt-4.1-nano",
                ),
                Slider(
                    id="temperature",
                    label="Temperature",
                    initial=defaults["temperature"],
                    min=0.0,
                    max=1.0,
                    step=0.1,
                ),
                Slider(
                    id="max_rounds",
                    label="Max Rounds",
                    initial=defaults["max_rounds"],
                    min=1,
                    max=20,
                    step=1,
                ),
                Switch(
                    id="streaming",
                    label="Enable Streaming",
                    initial=True,
                ),
            ]
        ).send()

        logger.info("Chat settings initialized successfully")

    async def handle_settings_update(self, settings: Any) -> None:
        """Update chat settings with new values.

        Args:
            settings: New chat settings (either ChatSettings object or dict)
        """
        current_settings = cl.user_session.get("settings", {}) or {}

        # Update each setting that was changed
        # Handle both Pydantic model (with dict() method) and regular dict
        if hasattr(settings, "dict") and callable(getattr(settings, "dict")):
            settings_dict = settings.dict()
        else:
            settings_dict = dict(settings)

        for key, value in settings_dict.items():
            if key in current_settings and current_settings[key] != value:
                logger.info(f"Setting '{key}' updated from {current_settings[key]} to {value}")
                current_settings[key] = value

        # Store updated settings
        cl.user_session.set("settings", current_settings)
        logger.info("Settings updated successfully")


@cl.set_chat_profiles
async def chat_profiles() -> list[cl.ChatProfile]:
    """Define enhanced chat profiles with metadata and icons.

    Returns:
        List of chat profiles
    """
    return [
        cl.ChatProfile(
            name="Magentic Fleet Fast",
            markdown_description=(
                "**Speed-Optimized Workflow**\n\n"
                "- Model: GPT-4.1 Nano (128k context)\n"
                "- Response Time: <2s average\n"
                "- Best for: Simple queries & quick tasks"
            ),
            icon="public/icons/rocket.svg",
        ),
        cl.ChatProfile(
            name="Magentic Fleet Standard",
            markdown_description=(
                "**Advanced Reasoning Suite**\n\n"
                "- Model: GPT-4.1 Mini (128k context)\n"
                "- Multi-agent collaboration\n"
                "- Complex problem solving"
            ),
            icon="public/icons/microscope.svg",
        ),
    ]
