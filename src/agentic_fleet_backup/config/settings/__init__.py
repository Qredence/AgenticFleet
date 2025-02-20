"""Application settings configuration for AgenticFleet."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Configuration file paths
SETTINGS_DIR = Path(__file__).parent
APP_SETTINGS_PATH = SETTINGS_DIR / "app_settings.yaml"

def load_app_settings() -> Dict[str, Any]:
    """Load application settings from YAML file.

    Returns:
        Dict containing application settings

    Raises:
        FileNotFoundError: If settings file doesn't exist
        yaml.YAMLError: If settings file is invalid
    """
    try:
        with open(APP_SETTINGS_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Settings file not found: {APP_SETTINGS_PATH}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing settings file {APP_SETTINGS_PATH}: {e}")

def get_required_env_vars() -> List[str]:
    """Get list of required environment variables.

    Returns:
        List of required environment variable names
    """
    settings = load_app_settings()
    return settings.get("required_env_vars", [])

def validate_env_vars() -> Optional[List[str]]:
    """Validate that all required environment variables are set.

    Returns:
        List of missing environment variables, or None if all are present
    """
    required_vars = get_required_env_vars()
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return missing_vars if missing_vars else None

def get_app_defaults() -> Dict[str, Any]:
    """Get default application settings.

    Returns:
        Dict containing default settings
    """
    settings = load_app_settings()
    return settings.get("defaults", {})

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration.

    Returns:
        Dict containing logging configuration
    """
    settings = load_app_settings()
    return settings.get("logging", {})

def get_security_config() -> Dict[str, Any]:
    """Get security configuration.

    Returns:
        Dict containing security configuration
    """
    settings = load_app_settings()
    return settings.get("security", {})

def get_environment_config() -> Dict[str, Any]:
    """Get environment configuration.

    Returns:
        Dict containing environment configuration
    """
    settings = load_app_settings()
    return settings.get("environment", {})

def get_performance_config() -> Dict[str, Any]:
    """Get performance configuration.

    Returns:
        Dict containing performance configuration
    """
    settings = load_app_settings()
    return settings.get("performance", {})

def get_api_config() -> Dict[str, Any]:
    """Get API configuration.

    Returns:
        Dict containing API configuration
    """
    settings = load_app_settings()
    return settings.get("api", {})

def get_app_info() -> Dict[str, Any]:
    """Get basic application information.

    Returns:
        Dict containing application information
    """
    settings = load_app_settings()
    return settings.get("app", {})

# Export configuration paths and functions
__all__ = [
    "APP_SETTINGS_PATH",
    "load_app_settings",
    "get_required_env_vars",
    "validate_env_vars",
    "get_app_defaults",
    "get_logging_config",
    "get_security_config",
    "get_environment_config",
    "get_performance_config",
    "get_api_config",
    "get_app_info"
]
