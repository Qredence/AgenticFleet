"""Chainlit UI components and settings."""

from typing import Any  # noqa: UP035

import chainlit as cl


def chat_profiles() -> list[dict[str, Any]]:
    """Define enhanced chat profiles with metadata and icons.

    Returns:
        List[Dict[str, Any]]: List of chat profile configurations
    """
    return [
        {
            "label": "🚀 Standard",
            "value": "standard",
            "description": "Basic chat with code generation and execution",
            "icon": "standard.png",
        },
        {
            "label": "🔬 Advanced",
            "value": "advanced",
            "description": "Enhanced capabilities with web search and file operations",
            "icon": "advanced.png",
        },
    ]


async def setup_chat_settings() -> None:
    """Initialize chat settings with default values."""
    settings = {"temperature": 0.7, "max_tokens": 2000, "stream": True}
    await cl.user_session.set("settings", settings)


async def update_settings(new_settings: dict[str, Any]) -> None:
    """Update chat settings with new values.

    Args:
        new_settings: Dictionary of settings to update
    """
    current = await cl.user_session.get("settings") or {}
    current.update(new_settings)
    await cl.user_session.set("settings", current)


def agent_input_widgets() -> list[cl.InputWidget]:
    """Generate Chainlit input widgets for agent configuration.

    Returns:
        List[cl.InputWidget]: List of input widgets
    """
    return [
        cl.Select(
            id="agent_type",
            label="Agent Type",
            values=["coder", "researcher", "planner"],
            initial_value="coder",
        ),
        cl.Slider(id="temperature", label="Temperature", min=0.0, max=1.0, step=0.1, initial=0.7),
    ]
