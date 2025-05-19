"""Tests for the ConfigurationManager class."""

from unittest.mock import patch

import pytest
from agentic_fleet.config import ConfigurationManager


@pytest.fixture
def mock_config_files():
    """Mock the configuration file loading functions."""
    with patch("agentic_fleet.config.load_all_configs") as mock_load_configs:
        mock_load_configs.return_value = {
            "llm": {
                "azure": {
                    "name": "Azure OpenAI",
                    "models": {
                        "gpt-4o": {
                            "model_name": "gpt-4o",
                            "context_length": 128000,
                            "model_info": {
                                "vision": True,
                                "function_calling": True,
                                "json_output": True,
                            },
                        }
                    },
                }
            },
            "agent": {
                "coder": {
                    "name": "Coding Agent",
                    "description": "Specialized in writing code",
                    "system_prompt": "You are a coding assistant.",
                }
            },
            "fleet": {
                "magentic_one": {"name": "MagenticOne", "agents": ["coder"], "max_rounds": 10}
            },
        }
        yield


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "WORKSPACE_DIR": "test_workspace",
        "DEBUG_DIR": "test_debug",
        "DOWNLOADS_DIR": "test_downloads",
        "LOGS_DIR": "test_logs",
        "STREAM_DELAY": "0.02",
        "USE_OAUTH": "true",
        "DEFAULT_MAX_ROUNDS": "15",
        "DEFAULT_MAX_TIME": "400",
        "DEFAULT_MAX_STALLS": "5",
        "DEFAULT_START_PAGE": "https://www.example.com",
        "DEFAULT_SYSTEM_PROMPT": "Test system prompt",
        "AZURE_OPENAI_ENDPOINT": "https://test-endpoint.com",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_API_VERSION": "2024-08-01",
    }

    with patch.dict("os.environ", env_vars, clear=False):
        yield


def test_config_manager_initialization():
    """Test that ConfigurationManager initializes correctly."""
    config_manager = ConfigurationManager()

    # Verify initial state
    assert hasattr(config_manager, "_llm_configs")
    assert hasattr(config_manager, "_agent_configs")
    assert hasattr(config_manager, "_fleet_configs")
    assert hasattr(config_manager, "_environment")
    assert hasattr(config_manager, "_security")
    assert hasattr(config_manager, "_defaults")


def test_load_all_with_valid_configs(mock_config_files, mock_env_vars):
    """Test loading all configurations with valid files and environment variables."""
    config_manager = ConfigurationManager()
    config_manager.load_all()

    # Verify configurations were loaded
    assert config_manager._llm_configs == mock_config_files.return_value["llm"]
    assert config_manager._agent_configs == mock_config_files.return_value["agent"]
    assert config_manager._fleet_configs == mock_config_files.return_value["fleet"]

    # Verify environment settings
    env_settings = config_manager.get_environment_settings()
    assert env_settings["workspace_dir"] == "test_workspace"
    assert env_settings["debug_dir"] == "test_debug"
    assert env_settings["downloads_dir"] == "test_downloads"
    assert env_settings["logs_dir"] == "test_logs"
    assert env_settings["stream_delay"] == 0.02

    # Verify security settings
    security_settings = config_manager.get_security_settings()
    assert security_settings["use_oauth"] is True

    # Verify default settings
    defaults = config_manager.get_defaults()
    assert defaults["max_rounds"] == 15
    assert defaults["max_time"] == 400
    assert defaults["max_stalls"] == 5
    assert defaults["start_page"] == "https://www.example.com"
    assert defaults["system_prompt"] == "Test system prompt"


def test_load_all_with_missing_files():
    """Test loading configurations when files are missing."""
    with patch(
        "agentic_fleet.config.load_all_configs", side_effect=FileNotFoundError("Test error")
    ):
        config_manager = ConfigurationManager()

        # Should not raise an exception
        config_manager.load_all()

        # Should initialize defaults
        assert len(config_manager._llm_configs) > 0
        assert isinstance(config_manager._agent_configs, dict)
        assert isinstance(config_manager._fleet_configs, dict)


def test_validate_environment_with_valid_env(mock_env_vars):
    """Test environment validation with valid environment variables."""
    with patch("agentic_fleet.config.validate_env_vars", return_value=None):
        config_manager = ConfigurationManager()

        # Should return None (no error)
        assert config_manager.validate_environment() is None


def test_validate_environment_with_invalid_env():
    """Test environment validation with missing environment variables."""
    with patch("agentic_fleet.config.validate_env_vars", return_value="Missing required variables"):
        config_manager = ConfigurationManager()

        # Should return error message
        assert config_manager.validate_environment() == "Missing required variables"


def test_get_model_settings(mock_config_files, mock_env_vars):
    """Test retrieving model settings."""
    config_manager = ConfigurationManager()
    config_manager.load_all()

    # Get settings for a specific model
    model_settings = config_manager.get_model_settings("azure", "gpt-4o")

    # Verify settings
    assert model_settings["model_name"] == "gpt-4o"
    assert model_settings["context_length"] == 128000
    assert model_settings["model_info"]["vision"] is True
    assert model_settings["model_info"]["function_calling"] is True


def test_get_agent_settings(mock_config_files, mock_env_vars):
    """Test retrieving agent settings."""
    config_manager = ConfigurationManager()
    config_manager.load_all()

    # Get settings for a specific agent
    agent_settings = config_manager.get_agent_settings("coder")

    # Verify settings
    assert agent_settings["name"] == "Coding Agent"
    assert agent_settings["description"] == "Specialized in writing code"
    assert agent_settings["system_prompt"] == "You are a coding assistant."


def test_get_team_settings(mock_config_files, mock_env_vars):
    """Test retrieving team settings."""
    config_manager = ConfigurationManager()
    config_manager.load_all()

    # Get settings for a specific team
    team_settings = config_manager.get_team_settings("magentic_one")

    # Verify settings
    assert team_settings["name"] == "MagenticOne"
    assert team_settings["agents"] == ["coder"]
    assert team_settings["max_rounds"] == 10
