"""Configuration management for AgenticFleet."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from agentic_fleet.config.models import (
    get_agent_config,
    get_model_config,
    get_team_config,
    load_all_configs,
)
from agentic_fleet.config.settings import (
    get_api_config,
    get_app_defaults,
    get_app_info,
    get_environment_config,
    get_logging_config,
    get_performance_config,
    get_security_config,
    load_app_settings,
    validate_env_vars,
)

# Configuration root directory
CONFIG_ROOT = Path(__file__).parent


class ConfigurationManager:
    """Manages configuration loading and access."""

    def __init__(self):
        self._llm_configs = {}
        self._agent_configs = {}
        self._fleet_configs = {}
        self._environment = {}
        self._security = {}
        self._defaults = {}

    def load_all(self):
        """Load all configuration files."""
        configs = load_all_configs()

        # Update configuration dictionaries
        self._llm_configs = configs["llm"]
        self._agent_configs = configs["agent"]  # Changed from agent_pool to agent
        self._fleet_configs = configs["fleet"]

        # Load environment settings
        self._environment = {
            "workspace_dir": os.getenv("WORKSPACE_DIR", "workspace"),
            "debug_dir": os.getenv("DEBUG_DIR", "debug"),
            "downloads_dir": os.getenv("DOWNLOADS_DIR", "downloads"),
            "logs_dir": os.getenv("LOGS_DIR", "logs"),
            "stream_delay": float(os.getenv("STREAM_DELAY", "0.01")),
        }

        # Load security settings
        self._security = {
            "use_oauth": os.getenv("USE_OAUTH", "false").lower() == "true",
            "oauth_providers": [],
        }

        # Load default settings
        self._defaults = {
            "max_rounds": int(os.getenv("DEFAULT_MAX_ROUNDS", "10")),
            "max_time": int(os.getenv("DEFAULT_MAX_TIME", "300")),
            "max_stalls": int(os.getenv("DEFAULT_MAX_STALLS", "3")),
            "start_page": os.getenv("DEFAULT_START_PAGE", "https://www.bing.com"),
            "system_prompt": os.getenv(
                "DEFAULT_SYSTEM_PROMPT", "You are a helpful AI assistant."
            ),
        }

    def validate_environment(self) -> Optional[str]:
        """Validate environment configuration."""
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_DEPLOYMENT",
        ]

        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            return f"Missing required environment variables: {', '.join(missing)}"
        return None

    def get_model_settings(
        self, provider: str, model_name: Optional[str] = None
    ) -> Dict:
        """Get model configuration settings."""
        return get_model_config(provider, model_name)

    def get_agent_settings(self, agent_name: str) -> Dict:
        """Get agent configuration settings."""
        return get_agent_config(agent_name)

    def get_team_settings(self, team_name: str) -> Dict:
        """Get team configuration settings."""
        return get_team_config(team_name)

    def get_environment_settings(self) -> Dict:
        """Get environment settings."""
        return self._environment

    def get_security_settings(self) -> Dict:
        """Get security settings."""
        return self._security

    def get_defaults(self) -> Dict:
        """Get default settings."""
        return self._defaults

    def get_app_settings(self) -> Dict:
        """Get application settings."""
        return load_app_settings()
    


# Create singleton instance
config_manager = ConfigurationManager()

# Load default values from app_settings.yaml
_app_settings = load_app_settings()
_defaults = _app_settings.get("defaults", {})

# Export default constants
DEFAULT_MAX_ROUNDS = _defaults.get("max_rounds", 10)
DEFAULT_MAX_TIME = _defaults.get("max_time", 300)
DEFAULT_MAX_STALLS = _defaults.get("max_stalls", 3)
DEFAULT_START_PAGE = _defaults.get("start_page", "https://www.bing.com")
DEFAULT_TEMPERATURE = _defaults.get("temperature", 0.7)
DEFAULT_SYSTEM_PROMPT = _defaults.get(
    "system_prompt", "You are a helpful AI assistant."
)

# Export configuration manager and paths
__all__ = [
    "CONFIG_ROOT",
    "ConfigurationManager",
    "config_manager",
    # Default constants
    "DEFAULT_MAX_ROUNDS",
    "DEFAULT_MAX_TIME",
    "DEFAULT_MAX_STALLS",
    "DEFAULT_START_PAGE",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_SYSTEM_PROMPT",
    # Re-export from models
    "get_model_config",
    "get_agent_config",
    "get_team_config",
    # Re-export from settings
    "get_app_defaults",
    "get_logging_config",
    "get_security_config",
    "get_environment_config",
    "get_performance_config",
    "get_api_config",
    "get_app_info",
]
