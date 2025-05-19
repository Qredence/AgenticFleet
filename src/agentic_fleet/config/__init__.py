"""Configuration management for AgenticFleet."""

import os
from pathlib import Path

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
from agentic_fleet.config.settings.models import (
    ApiConfig,
    CorsConfig,
    DefaultsConfig,
    EnvironmentConfig,
    LoggingConfig,
    OAuthProviderConfig,
    SecurityConfig,
)

# Configuration root directory
CONFIG_ROOT = Path(__file__).parent


class ConfigurationManager:
    """Manages configuration loading and access."""

    def __init__(self):
        self._llm_configs = {}
        self._agent_configs = {}
        self._fleet_configs = {}
        self._environment = None  # Will be EnvironmentConfig
        self._security = None
        self._defaults = None
        self._api = None
        self._cors = None
        self._logging = None

    def load_all(self):
        """Load all configuration files."""
        try:
            configs = load_all_configs()

            # Update configuration dictionaries
            self._llm_configs = configs["llm"]
            self._agent_configs = configs["agent"]
            self._fleet_configs = configs["fleet"]

            # Load app settings
            app_settings = load_app_settings()
            env_settings = app_settings.get("environment", {})
            defaults_settings = app_settings.get("defaults", {})
            security_settings = app_settings.get("security", {})
            api_settings = app_settings.get("api", {})
            cors_settings = app_settings.get("cors", {})
            logging_settings = app_settings.get("logging", {})

            # Typed config objects
            self._environment = EnvironmentConfig(**env_settings)
            self._defaults = DefaultsConfig(**defaults_settings)
            if "oauth_providers" in security_settings:
                security_settings["oauth_providers"] = [
                    OAuthProviderConfig(**prov) for prov in security_settings["oauth_providers"]
                ]
            self._security = SecurityConfig(**security_settings)
            self._api = ApiConfig(**api_settings)
            self._cors = CorsConfig(**cors_settings)
            self._logging = LoggingConfig(**logging_settings)

            # Ensure directories exist
            self._ensure_directories()

        except FileNotFoundError as e:
            print(f"Warning: Configuration file not found: {e}")
            print("Using default configurations...")
            self._initialize_defaults()
        except Exception as e:
            raise RuntimeError(f"Error loading configurations: {e}")

    def _initialize_defaults(self):
        """Initialize default configurations when files are missing."""
        self._llm_configs = {
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
        }
        self._agent_configs = {}
        self._fleet_configs = {}

    def validate_environment(self) -> str | None:
        """Validate environment configuration."""
        # Use the imported validate_env_vars function if available
        if "validate_env_vars" in globals():
            return validate_env_vars()

        # Fallback to the original implementation
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

    def get_model_settings(self, provider: str, model_name: str | None = None) -> dict:
        """Get model configuration settings."""
        return get_model_config(provider, model_name)

    def get_agent_settings(self, agent_name: str) -> dict:
        """Get agent configuration settings."""
        return get_agent_config(agent_name)

    def get_team_settings(self, team_name: str) -> dict:
        """Get team configuration settings."""
        return get_team_config(team_name)

    def get_environment_settings(self) -> EnvironmentConfig:
        """Get environment settings as a typed object."""
        return self._environment

    def get_defaults(self) -> DefaultsConfig:
        """Get default settings as a typed object."""
        return self._defaults

    def get_security_settings(self) -> SecurityConfig:
        """Get security settings as a typed object."""
        return self._security

    def get_api_settings(self) -> ApiConfig:
        return self._api

    def get_cors_settings(self) -> CorsConfig:
        return self._cors

    def get_logging_settings(self) -> LoggingConfig:
        return self._logging

    def get_app_settings(self) -> dict:
        """Get application settings."""
        return load_app_settings()

    def _ensure_directories(self):
        """Ensure that all required directories exist."""
        from agentic_fleet.core.utils import ensure_directory_exists

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent.parent

        # Create the .files directory if it doesn't exist
        files_dir = project_root / ".files"
        ensure_directory_exists(str(files_dir))

        # Create subdirectories
        for dir_key in ["workspace_dir", "debug_dir", "downloads_dir", "logs_dir"]:
            dir_path = self._environment.__dict__.get(dir_key, "")
            if dir_path:
                # Handle both absolute and relative paths
                if dir_path.startswith("./"):
                    # Relative path to project root
                    full_path = project_root / dir_path[2:]
                elif not os.path.isabs(dir_path):
                    # Relative path without ./
                    full_path = project_root / dir_path
                else:
                    # Absolute path
                    full_path = Path(dir_path)

                # Create the directory
                ensure_directory_exists(str(full_path))

                # Update the environment with the full path
                self._environment.__dict__[dir_key] = str(full_path)


# Create singleton instance
config_manager = ConfigurationManager()

# Initialize configuration
try:
    config_manager.load_all()
except Exception as e:
    print(f"Warning: Failed to initialize configuration: {e}")

# Load default values from app_settings.yaml
_app_settings = load_app_settings()
_defaults = _app_settings.get("defaults", {})

# Export default constants
DEFAULT_MAX_ROUNDS = _defaults.get("max_rounds", 10)
DEFAULT_MAX_TIME = _defaults.get("max_time", 300)
DEFAULT_MAX_STALLS = _defaults.get("max_stalls", 3)
DEFAULT_START_PAGE = _defaults.get("start_page", "https://www.bing.com")
DEFAULT_TEMPERATURE = _defaults.get("temperature", 0.7)
DEFAULT_SYSTEM_PROMPT = _defaults.get("system_prompt", "You are a helpful AI assistant.")

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
