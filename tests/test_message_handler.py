"""Tests for the message handler module."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from agentic_fleet.ui.message_handler import handle_chat_message


@pytest.mark.asyncio
async def test_handle_chat_message(mock_user_session, mock_chainlit_elements):
    """Test handling a chat message."""
    # Create mock message
    mock_message = MagicMock()
    mock_message.content = "Hello, I need help with a task"
    mock_message.id = "test_message_id"

    # Create mock agent team
    mock_team = MagicMock()
    mock_team.run_stream = AsyncMock(
        return_value=[
            {"content": "I'll help you with your task", "author": "Assistant"},
            {"content": "Here's a plan:\n1. Step one\n2. Step two", "author": "Planner"},
        ]
    )

    # Set up mock team in user session
    mock_user_session["team"] = mock_team

    # Setup mock Message class
    mock_message_instance = mock_chainlit_elements["Message"].return_value

    # Call the function
    await handle_chat_message(mock_message)

    # Check that run_stream was called with the message content
    mock_team.run_stream.assert_called_once_with(mock_message.content)

    # Check that messages were sent for each response from run_stream
    assert mock_chainlit_elements["Message"].call_count >= 2
    assert mock_message_instance.send.call_count >= 2


@pytest.mark.asyncio
async def test_handle_chat_message_with_reset(mock_user_session, mock_chainlit_elements):
    """Test handling a chat message with a reset command."""
    # Create mock message with reset command
    mock_message = MagicMock()
    mock_message.content = "/reset"
    mock_message.id = "test_message_id"

    # Create mock agent team
    mock_team = MagicMock()

    # Mock app_manager for reset operation
    mock_app_manager = MagicMock()
    mock_app_manager.reset_agent_team = AsyncMock()

    # Set up mocks in user session
    mock_user_session["team"] = mock_team
    mock_user_session["app_manager"] = mock_app_manager

    # Call the function
    await handle_chat_message(mock_message)

    # Check that reset_agent_team was called
    mock_app_manager.reset_agent_team.assert_called_once()

    # Verify that run_stream was not called (since this was a reset command)
    assert not mock_team.run_stream.called


@pytest.mark.asyncio
async def test_handle_chat_message_error(mock_user_session, mock_chainlit_elements):
    """Test handling errors during chat message processing."""
    # Create mock message
    mock_message = MagicMock()
    mock_message.content = "Hello, I need help with a task"
    mock_message.id = "test_message_id"

    # Create mock agent team that raises an exception
    mock_team = MagicMock()
    mock_team.run_stream = AsyncMock(side_effect=Exception("Test error"))

    # Set up mock team in user session
    mock_user_session["team"] = mock_team

    # Setup mock Message class
    mock_message_instance = mock_chainlit_elements["Message"].return_value

    # Call the function - should not raise an exception
    await handle_chat_message(mock_message)

    # Check that an error message was sent
    assert mock_chainlit_elements["Message"].called
    assert "error" in str(mock_chainlit_elements["Message"].call_args).lower()
