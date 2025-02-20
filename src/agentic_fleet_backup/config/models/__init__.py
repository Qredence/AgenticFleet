"""Configuration models and loaders for AgenticFleet."""

import os
from typing import Dict, Optional
import yaml

# Get the root directory of the package
PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Configuration file paths
LLM_CONFIG_PATH = os.path.join(PACKAGE_ROOT, '@llm_config.yaml')
AGENT_CONFIG_PATH = os.path.join(PACKAGE_ROOT, 'config', 'models', 'agent_pool.yaml')
FLEET_CONFIG_PATH = os.path.join(PACKAGE_ROOT, 'config', 'models', 'fleet_config.yaml')

def load_yaml_config(path: str) -> dict:
    """Load a YAML configuration file."""
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {path}")
    except Exception as e:
        raise Exception(f"Error loading configuration file {path}: {str(e)}")

def load_llm_config() -> dict:
    """Load the LLM configuration."""
    config = load_yaml_config(LLM_CONFIG_PATH)
    return config.get("Model", {})

def load_agent_config() -> dict:
    """Load the agent configuration."""
    return load_yaml_config(AGENT_CONFIG_PATH)

def load_fleet_config() -> Dict:
    """Load fleet configuration."""
    return load_yaml_config(FLEET_CONFIG_PATH)

def load_all_configs() -> dict:
    """Load all configuration files."""
    return {
        "llm": load_llm_config(),
        "agent": load_agent_config(),
        "fleet": load_fleet_config()
    }

def get_model_config(provider: str, model_name: Optional[str] = None) -> Dict:
    """Get configuration for specific model."""
    config = load_llm_config()
    provider_config = config.get("providers", {}).get(provider, {})
    
    if not model_name:
        return provider_config
        
    return provider_config.get("models", {}).get(model_name, {})

def get_agent_config(agent_name: str) -> Dict:
    """Get configuration for specific agent."""
    config = load_agent_config()
    return config.get("agents", {}).get(agent_name, {})

def get_team_config(team_name: str) -> Dict:
    """Get configuration for specific team."""
    config = load_fleet_config()
    return config.get("teams", {}).get(team_name, {})

# Export configuration paths
__all__ = [
    "LLM_CONFIG_PATH",
    "AGENT_CONFIG_PATH",
    "FLEET_CONFIG_PATH",
    "load_yaml_config",
    "load_llm_config",
    "load_agent_config",
    "load_fleet_config",
    "load_all_configs",
    "get_model_config",
    "get_agent_config",
    "get_team_config"
]
