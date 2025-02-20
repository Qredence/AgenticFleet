"""Chat settings management for Agentic Fleet."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import chainlit as cl
from chainlit.context import context
from chainlit.input_widget import InputWidget

from agentic_fleet.config import (
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MAX_STALLS,
    DEFAULT_MAX_TIME,
    DEFAULT_START_PAGE,
    DEFAULT_TEMPERATURE,
    DEFAULT_SYSTEM_PROMPT,
    config_manager
)


@dataclass
class ChatSettings:
    """Manages chat settings with integrated fleet and model configurations."""

    inputs: List[InputWidget] = field(default_factory=list)
    _settings: Dict[str, Any] = field(default_factory=dict)

    def __init__(self) -> None:
        """Initialize chat settings with default configuration."""
        # Get model configuration
        model_config = config_manager.get_model_settings("azure")
        available_models = [
            {"label": model.get("name", "").upper(), "value": model.get("name", "")}
            for model in model_config.get("models", {}).values()
        ] or [
            {"label": "O3-Mini", "value": "o3-mini"},
            {"label": "GPT-4O-Mini", "value": "gpt-4o-mini"},
            {"label": "GPT-3.5 Turbo", "value": "gpt-3.5-turbo"}
        ]

        self.inputs = [
            # Fleet Configuration
            cl.Select(
                id="fleet_mode",
                label="Fleet Mode",
                value="collaborative",
                items=[
                    {"label": "Collaborative", "value": "collaborative"},
                    {"label": "Competitive", "value": "competitive"},
                    {"label": "Hybrid", "value": "hybrid"}
                ],
                description="Mode of operation for the agent fleet",
            ),
            cl.Slider(
                id="max_rounds",
                label="Max Conversation Rounds",
                value=DEFAULT_MAX_ROUNDS,
                min=1,
                max=100,
                step=1,
                description="Maximum number of conversation rounds between agents",
            ),
            cl.Slider(
                id="max_time",
                label="Max Time (Minutes)",
                value=DEFAULT_MAX_TIME,
                min=1,
                max=60,
                step=1,
                description="Maximum time allowed for task completion",
            ),
            cl.Slider(
                id="max_stalls",
                label="Max Stalls Before Replan",
                value=DEFAULT_MAX_STALLS,
                min=1,
                max=10,
                step=1,
                description="Maximum number of stalls before triggering replanning",
            ),
            # Model Configuration
            cl.Select(
                id="model_name",
                label="Model",
                value="o3-mini",
                items=available_models,
                description="Language model to use",
            ),
            cl.Slider(
                id="temperature",
                label="Temperature",
                value=DEFAULT_TEMPERATURE,
                min=0.0,
                max=2.0,
                step=0.1,
                description="Controls randomness in model responses",
            ),
            cl.TextInput(
                id="system_prompt",
                label="System Prompt",
                value=DEFAULT_SYSTEM_PROMPT,
                description="Base prompt for the AI model",
            ),
            # Web Navigation
            cl.TextInput(
                id="start_page",
                label="Start Page URL",
                value=DEFAULT_START_PAGE,
                description="Default starting URL for web searches",
            ),
            cl.Slider(
                id="max_pages",
                label="Max Pages",
                value=5,
                min=1,
                max=20,
                step=1,
                description="Maximum number of pages to visit per search",
            ),
        ]
        self._settings = {
            input_widget.id: input_widget.value for input_widget in self.inputs
        }

    @property
    def settings(self) -> Dict[str, Any]:
        """Get current settings values."""
        return self._settings

    def update(self, new_settings: Dict[str, Any]) -> None:
        """Update settings with new values."""
        for key, value in new_settings.items():
            if key in self._settings:
                self._settings[key] = value
                # Update the corresponding input widget
                for input_widget in self.inputs:
                    if input_widget.id == key:
                        input_widget.value = value
                        break

    async def send(self) -> Dict[str, Any]:
        """Send settings to the UI and return current settings."""
        context.emitter.set_chat_settings(self.settings)
        inputs_content = [input_widget.to_dict() for input_widget in self.inputs]
        await context.emitter.emit("chat_settings", inputs_content)
        return self.settings

    def get_fleet_config(self) -> Dict[str, Any]:
        """Get configuration specific to fleet behavior."""
        return {
            "mode": self._settings["fleet_mode"],
            "max_rounds": self._settings["max_rounds"],
            "max_time": self._settings["max_time"],
            "max_stalls": self._settings["max_stalls"],
        }

    def get_model_config(self) -> Dict[str, Any]:
        """Get configuration specific to the model."""
        model_settings = config_manager.get_model_settings(
            "azure", self._settings["model_name"]
        )
        return {
            "model": self._settings["model_name"],
            "temperature": self._settings["temperature"],
            "system_prompt": self._settings["system_prompt"],
            **model_settings
        }

    def get_web_config(self) -> Dict[str, Any]:
        """Get configuration specific to web navigation."""
        return {
            "start_page": self._settings["start_page"],
            "max_pages": self._settings["max_pages"],
        }

    def get_agent_config(self) -> Dict[str, Any]:
        """Get combined configuration for agent initialization."""
        return {
            **self.get_fleet_config(),
            **self.get_model_config(),
            "web_config": self.get_web_config(),
        }
