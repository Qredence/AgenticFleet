"""Chainlit UI event handlers."""

import logging
from typing import Any

import chainlit as cl

from agentic_fleet.apps.chainlit_ui.agent_registry.default_agents import (
    initialize_default_agents,
)
from agentic_fleet.core.application.manager import ApplicationManager


async def initialize_chat() -> None:
    """Initialize chat session with configured agents and settings."""
    try:
        # Get profile selection
        profile = await cl.AskForOption(
            content="Choose a chat profile:", options=chat_profiles(), timeout=180
        )

        # Store profile in session
        await cl.user_session.set("chat_profile", profile)

        # Initialize agents
        app_manager = ApplicationManager.get_instance()
        agents = initialize_default_agents(app_manager.model_client)
        # Use the first agent as the team for streaming compatibility
        team = agents[0] if agents else None

        # Store team in session
        await cl.user_session.set("agent_team", team)

        # Setup UI
        await setup_chat_settings()

    except Exception as e:
        logging.error(f"Chat initialization failed: {e}")
        await handle_processing_error(e)


async def process_message(message: cl.Message) -> None:
    """Process incoming chat message.

    Args:
        message: Incoming Chainlit message
    """
    try:
        # Get session data
        team = await cl.user_session.get("agent_team")
        if not team:
            raise ValueError("No agent team found in session")

        # Initialize task tracking
        task_ledger = cl.TaskList()
        task_status = {}

        # Process message
        await handle_message(message, team, task_ledger, task_status)

    except Exception as e:
        logging.error(f"Message processing failed: {e}")
        await handle_processing_error(e)


async def handle_message(
    message: cl.Message, team: Any, task_ledger: cl.TaskList, task_status: dict[str, cl.Text]
) -> None:
    """Handle chat message processing.

    Args:
        message: Incoming message
        team: Agent team
        task_ledger: Task tracking list
        task_status: Task status dictionary
    """
    # Format message
    formatted_content = format_message_content(message.content)

    # Extract and display task plan
    await display_task_plan(formatted_content, task_status, message.id)

    # Run agent team
    await run_team(team, formatted_content, task_ledger, task_status, message.id)


def format_message_content(content: str) -> str:
    """Format message content with proper markdown and structure.

    Args:
        content: Raw message content

    Returns:
        str: Formatted content
    """
    # Remove extra whitespace
    content = content.strip()

    # Add code block formatting if needed
    if content.startswith("```") and content.endswith("```"):
        return content

    return content


async def handle_processing_error(error: Exception) -> None:
    """Handle processing errors with proper formatting.

    Args:
        error: Exception that occurred
    """
    error_msg = f"Error: {str(error)}"
    if hasattr(error, "__traceback__"):
        error_msg += f"\n```python\n{traceback.format_exc()}\n```"

    await cl.Message(content=error_msg, author="system", type="error").send()
