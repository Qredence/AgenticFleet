"""Tests for the integration of agent teams with the application."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agentic_fleet.app import start_chat


@pytest.mark.asyncio
async def test_magentic_one_initialization(
    mock_user_session, mock_chainlit_elements, mock_env_vars, mock_openai_client
):
    """Test that MagenticOne is properly initialized with the correct parameters."""
    # Mock cl.ChatProfile
    mock_profile = MagicMock()
    mock_profile.name = "Test Profile"
    mock_profile.markdown_description = "Test description"
    mock_profile.model_settings = {"model_name": "gpt-4o-mini-2024-07-18"}

    # Mock the application manager
    with patch("agentic_fleet.app.ApplicationManager") as mock_app_manager_class:
        mock_app_manager = mock_app_manager_class.return_value
        mock_app_manager.start = AsyncMock()

        # Mock the MagenticOne team
        with patch("agentic_fleet.app.MagenticOne") as mock_team_class:
            mock_team = mock_team_class.return_value

            # Mock the LocalCommandLineCodeExecutor
            with patch("agentic_fleet.app.LocalCommandLineCodeExecutor") as mock_executor_class:
                mock_executor = mock_executor_class.return_value

                # Mock config_manager
                with patch("agentic_fleet.app.config_manager") as mock_config_manager:
                    mock_config_manager.get_environment_settings.return_value = {
                        "max_rounds": "15",
                        "max_time": "400",
                        "max_stalls": "5",
                        "temperature": "0.8",
                        "system_prompt": "Test system prompt",
                        "debug": True,
                    }
                    mock_config_manager.validate_environment.return_value = None
                    mock_config_manager.load_all = MagicMock()

                    # Mock chainlit.user_session
                    with patch("chainlit.user_session", mock_user_session):
                        # Call the function
                        await start_chat(mock_profile)

                        # Verify the application manager was started
                        mock_app_manager.start.assert_called_once()

                        # Verify MagenticOne was initialized with the correct parameters
                        mock_team_class.assert_called_once()
                        call_kwargs = mock_team_class.call_args.kwargs

                        assert call_kwargs["client"] == mock_openai_client
                        assert call_kwargs["max_rounds"] == 15
                        assert call_kwargs["max_time"] == 400
                        assert call_kwargs["max_stalls"] == 5
                        assert call_kwargs["temperature"] == 0.8
                        assert call_kwargs["system_prompt"] == "Test system prompt"
                        assert call_kwargs["debug"] is True

                        # Verify that the team was stored in the user session
                        assert mock_user_session["agent_team"] == mock_team


@pytest.mark.asyncio
async def test_magentic_one_with_default_values(
    mock_user_session, mock_chainlit_elements, mock_env_vars, mock_openai_client
):
    """Test that MagenticOne uses default values when environment settings are missing."""
    # Mock cl.ChatProfile
    mock_profile = MagicMock()
    mock_profile.name = "Test Profile"
    mock_profile.markdown_description = "Test description"
    mock_profile.model_settings = {"model_name": "gpt-4o-mini-2024-07-18"}

    # Mock the application manager
    with patch("agentic_fleet.app.ApplicationManager") as mock_app_manager_class:
        mock_app_manager = mock_app_manager_class.return_value
        mock_app_manager.start = AsyncMock()

        # Mock the MagenticOne team
        with patch("agentic_fleet.app.MagenticOne") as mock_team_class:
            mock_team = mock_team_class.return_value

            # Mock the LocalCommandLineCodeExecutor
            with patch("agentic_fleet.app.LocalCommandLineCodeExecutor") as mock_executor_class:
                mock_executor = mock_executor_class.return_value

                # Mock config_manager with empty settings
                with patch("agentic_fleet.app.config_manager") as mock_config_manager:
                    mock_config_manager.get_environment_settings.return_value = {}
                    mock_config_manager.validate_environment.return_value = None
                    mock_config_manager.load_all = MagicMock()

                    # Mock chainlit.user_session
                    with patch("chainlit.user_session", mock_user_session):
                        # Call the function
                        await start_chat(mock_profile)

                        # Verify MagenticOne was initialized with default parameters
                        mock_team_class.assert_called_once()
                        call_kwargs = mock_team_class.call_args.kwargs

                        assert call_kwargs["client"] == mock_openai_client
                        assert call_kwargs["max_rounds"] == 10  # Default value
                        assert call_kwargs["max_time"] == 300  # Default value
                        assert call_kwargs["max_stalls"] == 3  # Default value
                        assert call_kwargs["temperature"] == 0.7  # Default value
                        assert call_kwargs["system_prompt"] == ""  # Default value
                        assert call_kwargs["debug"] is False  # Default value


@pytest.mark.asyncio
async def test_agent_team_in_message_handling(mock_user_session, mock_chainlit_elements):
    """Test that the agent team is properly used in message handling."""
    # Create mock message
    mock_message = MagicMock()
    mock_message.content = "Hello, I need help with a task"

    # Create mock agent team
    mock_team = MagicMock()
    mock_team.run_stream = AsyncMock(
        return_value=[{"content": "I'll help you with your task", "author": "Assistant"}]
    )

    # Set up mock team in user session
    mock_user_session["agent_team"] = mock_team

    # Mock chainlit.user_session
    with patch("chainlit.user_session", mock_user_session):
        # Patch the message handler
        with patch("agentic_fleet.ui.message_handler.handle_chat_message") as mock_handler:
            # Import the function to test
            from agentic_fleet.app import message_handler

            # Call the function
            await message_handler(mock_message)

            # Verify handle_chat_message was called with the message
            mock_handler.assert_called_once_with(mock_message)
