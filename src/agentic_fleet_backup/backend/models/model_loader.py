"""Model loader module for AgenticFleet.

This module provides functionality for loading and configuring model clients
from configuration files and environment variables.
"""

import os
from importlib import import_module
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_model_config(config_path: str = None) -> Dict[str, Any]:
    """Load model configuration from YAML file.

    Args:
        config_path: Optional path to config file. If not provided, uses default.

    Returns:
        Dictionary containing model configuration
    """
    if not config_path:
        config_path = os.path.join(
            os.path.dirname(__file__),
            "model_config.yaml"
        )

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Model config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Resolve environment variables in config
    def resolve_env_vars(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, value)
        return value

    def deep_resolve(obj):
        if isinstance(obj, dict):
            return {k: deep_resolve(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [deep_resolve(item) for item in obj]
        else:
            return resolve_env_vars(obj)

    return deep_resolve(config)

def create_model_client(model_config: Dict[str, Any]) -> Any:
    """Create a model client based on the configuration.

    Args:
        model_config: Model configuration dictionary

    Returns:
        Model client instance
    """
    provider = model_config.get("provider")
    config = model_config.get("config", {})

    # Import the provider class dynamically
    module_path, class_name = provider.rsplit(".", 1)
    module = import_module(module_path)
    client_class = getattr(module, class_name)

    return client_class(**config)

def get_azure_model_client() -> Any:
    """Get the Azure OpenAI model client from the configuration.

    Returns:
        Configured Azure OpenAI client
    """
    config = load_model_config()
    azure_config = config.get("azure", {})
    return create_model_client(azure_config)
