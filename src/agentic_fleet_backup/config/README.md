# AgenticFleet Configuration System

This directory contains the configuration management system for AgenticFleet. The system is organized into two main components:

## 1. Models Configuration (`models/`)

Contains configurations for language models, agent pools, and fleet settings:

- `llm_config.yaml`: Language model configurations for different providers (Azure, OpenAI, Gemini)
  - Model capabilities and settings
  - Provider-specific configurations
  - Default parameters

- `agent_pool.yaml`: Available agent configurations
  - Agent types and capabilities
  - Default settings for each agent
  - Team compositions

- `fleet_config.yaml`: Fleet-wide settings and workflows
  - Workflow definitions
  - Chat profiles
  - OAuth settings
  - Monitoring configuration

## 2. Application Settings (`settings/`)

Contains application-wide settings and environment configurations:

- `app_settings.yaml`: Core application settings
  - Environment variables
  - API configurations
  - Security settings
  - Logging configurations
  - Performance settings

## Usage

The configuration system is accessed through the `ConfigurationManager` class:

```python
from agentic_fleet.config import config_manager

# Load all configurations
config_manager.load_all()

# Get model settings
model_config = config_manager.get_model_settings("azure", "o3-mini")

# Get agent settings
agent_config = config_manager.get_agent_settings("web_surfer")

# Get environment settings
env_config = config_manager.get_environment_settings()

# Validate environment
if error := config_manager.validate_environment():
    raise ValueError(error)
```

## Configuration Files

### 1. Model Configuration (`llm_config.yaml`)
```yaml
providers:
  azure:
    name: "Azure OpenAI"
    models:
      o3-mini:
        name: "o3-mini"
        context_length: 128000
        vision: true
        function_calling: true
```

### 2. Agent Pool Configuration (`agent_pool.yaml`)
```yaml
agents:
  web_surfer:
    name: "WebSurfer"
    type: "MultimodalWebSurfer"
    description: "Expert web surfer agent..."
    config:
      downloads_folder: "./files/downloads"
```

### 3. Fleet Configuration (`fleet_config.yaml`)
```yaml
workflows:
  default:
    name: "Standard Workflow"
    steps:
      - name: "Task Analysis"
        agent: "file_surfer"
```

### 4. Application Settings (`app_settings.yaml`)
```yaml
app:
  name: "AgenticFleet"
  version: "0.4.80"
environment:
  debug: false
  workspace_dir: "./files/workspace"
```

## Adding New Configurations

1. Add new settings to the appropriate YAML file
2. Update type hints and validation in the configuration manager
3. Add helper methods to access the new settings if needed
4. Document the new settings in this README

## Environment Variables

Required environment variables are defined in `app_settings.yaml`. The configuration system will validate these at startup:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`

## Best Practices

1. Always use the configuration manager to access settings
2. Keep sensitive information in environment variables
3. Use type hints and validation for new settings
4. Document any changes to the configuration structure
5. Keep YAML files organized and well-commented
