# Configuration Guide

This guide covers all configuration options available in AgenticFleet.

## Environment Variables

### Required Settings

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_OPENAI_MODEL=your_model
```

### Optional Settings

```env
# Server Configuration
HOST=localhost
PORT=8000
DEBUG=false

# Authentication
USE_OAUTH=false
OAUTH_GITHUB_CLIENT_ID=your_client_id
OAUTH_GITHUB_CLIENT_SECRET=your_client_secret

# Logging
LOG_LEVEL=INFO
LOG_FILE=agenticfleet.log

# Cache Configuration
CACHE_TYPE=memory
CACHE_DIR=.cache
CACHE_TTL=3600

# Model Provider Settings
MODEL_PROVIDER=azure  # Options: azure, openai, anthropic, local
```

## Command Line Arguments

AgenticFleet supports various command-line arguments that override environment variables:

```bash
# Basic Configuration
--host TEXT          Host to bind to
--port INTEGER       Port to bind to
--debug             Enable debug mode

# Authentication
--no-oauth          Disable OAuth authentication
--oauth-provider    OAuth provider to use (default: github)

# Logging
--log-level TEXT    Logging level (default: INFO)
--log-file TEXT     Log file path

# Cache
--cache-type TEXT   Cache type to use
--cache-dir TEXT    Cache directory path
--cache-ttl INTEGER Cache TTL in seconds
```

## Configuration File

You can also use a YAML configuration file:

```yaml
# config.yaml
server:
  host: localhost
  port: 8000
  debug: false

auth:
  use_oauth: true
  provider: github
  client_id: your_client_id
  client_secret: your_client_secret

logging:
  level: INFO
  file: agenticfleet.log

cache:
  type: memory
  dir: .cache
  ttl: 3600

model:
  provider: azure
  settings:
    api_key: your_api_key
    endpoint: your_endpoint
    deployment: your_deployment
    model: your_model
```

## Configuration Precedence

Configuration values are loaded in the following order (later values override earlier ones):

1. Default values
2. Configuration file
3. Environment variables
4. Command line arguments

## Advanced Configuration

### Custom Model Providers

To use a custom model provider:

1. Create a provider class that implements the required interface
2. Register the provider in your configuration:

```python
from agentic_fleet.core.models import register_provider

@register_provider("custom")
class CustomProvider:
    def __init__(self, **kwargs):
        # Initialize your provider
        pass

    async def generate(self, prompt: str) -> str:
        # Implement generation logic
        pass
```

### Proxy Configuration

For environments behind a proxy:

```env
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=https://proxy:port
NO_PROXY=localhost,127.0.0.1
```

### SSL Configuration

For HTTPS support:

```env
SSL_CERT_FILE=path/to/cert.pem
SSL_KEY_FILE=path/to/key.pem
```

## Environment-Specific Configuration

You can maintain different configurations for different environments:

```bash
# Development
.env.development

# Production
.env.production

# Testing
.env.test
```

Load specific environment:

```bash
ENV=production agenticfleet start
```
