"""Unit tests for the chainlit application.

Tests cover basic functionality of the chainlit app, including:
- Message sanitization and formatting
- Error handling
- Settings management
"""

from __future__ import annotations

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agentic_fleet.chainlit_app import (
    clean_error_message,
    error_handler,
    format_agent_name,
    handle_settings_update,
    on_action_reset,
    sanitize_html,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# This test has been removed as get_profile_metadata function is no longer available


def test_on_action_reset_functionality() -> None:
    """Test that on_action_reset calls the correct function.

    This test simply verifies that on_action_reset delegates to the UI message
    handler's on_reset function. We can't test the actual execution due to
    Chainlit context dependencies.
    """
    # Get the source code of on_action_reset to verify it calls on_reset
    source = inspect.getsource(on_action_reset)

    # Verify that the function calls the message handler's on_reset
    assert "await on_reset(action)" in source


def test_handle_settings_update_functionality() -> None:
    """Test that handle_settings_update updates the correct settings.

    This test verifies the logic of handle_settings_update by checking its
    source code rather than executing it, since execution requires Chainlit context.
    """
    # Get the source code of handle_settings_update to verify its logic
    source = inspect.getsource(handle_settings_update)

    # Verify that the function calls chainlit.user_session.set for each setting
    assert "user_session.set" in source

    # Verify it handles the settings we're interested in
    for setting in ["max_rounds", "max_time", "max_stalls", "start_page"]:
        assert setting in source


def test_sanitize_html() -> None:
    """Test HTML sanitization function."""
    # Test basic HTML escaping
    input_text = "<script>alert('xss')</script>"
    result = sanitize_html(input_text)
    # Verify that HTML tags are escaped
    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
    # The exact escaping of quotes might vary, but the content should be present
    assert "alert" in result

    # Test handling of None input - sanitize_html returns empty string for None
    assert sanitize_html(None) == ""

    # Test handling of non-string input
    assert sanitize_html(123) == "123"

    # Test error traceback formatting
    traceback_text = (
        "Something went wrong\nTraceback (most recent call last)\n"
        '  File "test.py", line 1\nValueError: test error'
    )
    result = sanitize_html(traceback_text)
    assert "<details>" in result
    assert "<summary>🐞 <b>Error details</b>" in result
    assert "<pre>Traceback" in result


def test_format_agent_name() -> None:
    """Test agent name formatting."""
    # Test normal name
    assert format_agent_name("AgentName") == "AgentName"

    # Test with UUID suffix that should be removed
    assert format_agent_name("AgentName_12345678-1234-1234-1234-123456789abc") == "AgentName"

    # Test with None/empty/unknown
    assert format_agent_name(None) == "Agent"
    assert format_agent_name("") == "Agent"
    assert format_agent_name("unknown") == "Agent"
    assert format_agent_name("none") == "Agent"


def test_clean_error_message() -> None:
    """Test error message cleaning."""
    # Test with error message that includes a traceback
    error_msg = "Error occurred: ValueError\nTraceback (most recent call last)\n..."
    result = clean_error_message(error_msg)

    # The function should return a sanitized version of the error message
    # Verify that the result contains the original content
    assert "Error occurred" in result
    assert "ValueError" in result

    # If the clean_error_message function does any truncation, we'd test that here
    # but for now we're just making sure it returns a non-empty string
    assert result is not None
    assert len(result) > 0


@pytest.mark.asyncio
async def test_error_handler_decorator() -> None:
    """Test the error_handler decorator properly catches and handles errors."""
    # Create a mock function that will raise an exception
    mock_func = AsyncMock(side_effect=ValueError("Test error"))
    decorated_func = error_handler(mock_func)

    # Create a mock for cl.Message
    mock_msg = MagicMock()

    # Mock Chainlit's Message class and our _send_message_with_avatar function
    with (
        patch("chainlit.Message") as mock_cl_message,
        patch("agentic_fleet.chainlit_app._send_message_with_avatar"),
    ):
        # Configure mock_cl_message so it doesn't need context
        mock_message_instance = MagicMock()
        mock_cl_message.return_value = mock_message_instance
        mock_cl_message.return_value.send = AsyncMock()

        # Mock logger to avoid actual logging
        with patch("agentic_fleet.chainlit_app.logger") as mock_logger:
            # Call the decorated function
            await decorated_func(1, 2, msg=mock_msg, test="test")

            # Verify function was called with correct parameters
            mock_func.assert_called_once_with(1, 2, msg=mock_msg, test="test")

            # Verify the error was logged
            assert any("Test error" in str(call) for call in mock_logger.error.call_args_list)


def test_message_processing_components() -> None:
    """Test the components used in message processing."""
    # Test format_agent_name which is used in process_message
    name = "TestAgent_12345678-1234-1234-1234-123456789abc"
    assert format_agent_name(name) == "TestAgent"

    # Test that sanitize_html correctly escapes HTML
    assert "&lt;" in sanitize_html("<script>")

    # Test that clean_error_message returns a string
    error_msg = "Error: Something went wrong"
    assert isinstance(clean_error_message(error_msg), str)
