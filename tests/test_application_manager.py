"""Tests for the ApplicationManager class."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agentic_fleet.core.application.manager import ApplicationConfig, ApplicationManager


@pytest.fixture
def mock_application_config():
    """Create a mock ApplicationConfig for testing."""
    return ApplicationConfig(project_root=Path("/test/project"), debug=True, log_level="DEBUG")


@pytest.mark.asyncio
async def test_application_manager_initialization(mock_application_config):
    """Test that ApplicationManager initializes correctly."""
    # Mock environment variables for the AzureOpenAIChatCompletionClient
    with patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_BASE": "https://test-endpoint.com",
            "AZURE_OPENAI_API_VERSION": "2024-08-01",
        },
    ):
        # Create the application manager
        app_manager = ApplicationManager(mock_application_config)

        # Verify the configuration was stored
        assert app_manager.config == mock_application_config
        assert app_manager._initialized is False
        assert hasattr(app_manager, "model_client")


@pytest.mark.asyncio
async def test_application_manager_initialize():
    """Test that ApplicationManager.initialize initializes resources correctly."""
    # Create a mock config
    mock_config = MagicMock()
    mock_config.debug = True
    mock_config.log_level = "DEBUG"
    mock_config.project_root = Path("/test/project")

    # Mock environment variables for the AzureOpenAIChatCompletionClient
    with patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_BASE": "https://test-endpoint.com",
            "AZURE_OPENAI_API_VERSION": "2024-08-01",
        },
    ):
        # Create the application manager
        app_manager = ApplicationManager(mock_config)

        # Call initialize
        await app_manager.initialize()

        # Verify initialization was successful
        assert app_manager._initialized is True


@pytest.mark.asyncio
async def test_application_manager_start():
    """Test that ApplicationManager.start initializes resources correctly."""
    # Create a mock config
    mock_config = MagicMock()
    mock_config.debug = True
    mock_config.log_level = "DEBUG"
    mock_config.project_root = Path("/test/project")

    # Mock environment variables for the AzureOpenAIChatCompletionClient
    with patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_BASE": "https://test-endpoint.com",
            "AZURE_OPENAI_API_VERSION": "2024-08-01",
        },
    ):
        # Create the application manager
        app_manager = ApplicationManager(mock_config)

        # Mock the initialize method
        app_manager.initialize = AsyncMock()

        # Call start
        await app_manager.start()

        # Verify initialize was called
        app_manager.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_application_manager_shutdown():
    """Test that ApplicationManager.shutdown cleans up resources correctly."""
    # Create a mock config
    mock_config = MagicMock()

    # Mock environment variables for the AzureOpenAIChatCompletionClient
    with patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_BASE": "https://test-endpoint.com",
            "AZURE_OPENAI_API_VERSION": "2024-08-01",
        },
    ):
        # Create the application manager
        app_manager = ApplicationManager(mock_config)

        # Set initialized to True
        app_manager._initialized = True

        # Call shutdown
        await app_manager.shutdown()

        # Verify initialized is set to False
        assert app_manager._initialized is False


@pytest.mark.asyncio
async def test_create_application():
    """Test that create_application creates an ApplicationManager instance."""
    from agentic_fleet.core.application.manager import create_application

    # Mock environment variables for the AzureOpenAIChatCompletionClient
    with patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_API_BASE": "https://test-endpoint.com",
            "AZURE_OPENAI_API_VERSION": "2024-08-01",
        },
    ):
        # Call create_application
        app_manager = create_application()

        # Verify the returned object is an ApplicationManager
        assert isinstance(app_manager, ApplicationManager)
        assert hasattr(app_manager, "config")
        assert isinstance(app_manager.config, ApplicationConfig)


@pytest.mark.asyncio
async def test_reset_agent_team(mock_user_session):
    """Test that reset_agent_team properly resets the agent team."""
    # Create a mock config
    mock_config = MagicMock()

    # Create the application manager
    app_manager = ApplicationManager(mock_config)

    # Create a mock agent team
    mock_team = MagicMock()
    mock_team.reset = AsyncMock()

    # Set up mock team in user session
    mock_user_session["agent_team"] = mock_team

    # Call reset_agent_team
    await app_manager.reset_agent_team()

    # Verify team.reset was called
    mock_team.reset.assert_called_once()


@pytest.mark.asyncio
async def test_reset_agent_team_no_team(mock_user_session):
    """Test that reset_agent_team handles the case when no team exists."""
    # Create a mock config
    mock_config = MagicMock()

    # Create the application manager
    app_manager = ApplicationManager(mock_config)

    # Ensure no team in session
    mock_user_session.pop("agent_team", None)

    # Call reset_agent_team - should not raise an exception
    await app_manager.reset_agent_team()

    # No assertions needed - we're just making sure it doesn't crash
