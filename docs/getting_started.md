# Getting Started with AgenticFleet

This guide will help you get up and running with AgenticFleet quickly.

## Prerequisites

- Python 3.10 or higher
- `uv` package manager (recommended) or `pip`
- A supported model provider (Azure OpenAI, OpenAI, or others)

## Installation

1. **Install AgenticFleet:**

   ```bash
   uv pip install agentic-fleet
   ```

2. **Install Browser Dependencies:**
   ```bash
   uv pip install playwright
   playwright install --with-deps chromium
   ```

## Environment Setup

1. **Create Environment File:**

   ```bash
   cp .env.example .env
   ```

2. **Configure Environment Variables:**
   Open `.env` and set these required variables:

   ```env
   # Required: Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_DEPLOYMENT=your_deployment
   AZURE_OPENAI_MODEL=your_model

   # Optional: OAuth Configuration (if using authentication)
   USE_OAUTH=true
   OAUTH_GITHUB_CLIENT_ID=your_client_id
   OAUTH_GITHUB_CLIENT_SECRET=your_client_secret
   ```

## Running AgenticFleet

### Using CLI (Recommended)

1. **Start with Default Settings:**

   ```bash
   agenticfleet start
   ```

2. **Start Without OAuth:**

   ```bash
   agenticfleet start no-oauth
   ```

3. **Custom Host and Port:**
   ```bash
   agenticfleet start --host localhost --port 8000
   ```

### Using Scripts

1. **Shell Script:**

   ```bash
   ./scripts/run.sh
   ```

2. **Python Script:**
   ```bash
   python scripts/run_direct.py
   ```

### Using Docker

1. **Pull the Image:**

   ```bash
   docker pull qredence/agenticfleet:latest
   ```

2. **Run the Container:**
   ```bash
   docker run -d -p 8001:8001 \
     -e AZURE_OPENAI_API_KEY=your_key \
     -e AZURE_OPENAI_ENDPOINT=your_endpoint \
     -e AZURE_OPENAI_DEPLOYMENT=your_deployment \
     -e AZURE_OPENAI_MODEL=your_model \
     qredence/agenticfleet:latest
   ```

## Verifying Installation

1. Start AgenticFleet using any of the methods above
2. Open your browser to `http://localhost:8000` (or your configured port)
3. You should see the AgenticFleet interface

## Next Steps

- Read the [Configuration Guide](configuration.md) for detailed settings
- Check out the [CLI Commands Reference](cli_commands.md) for available commands
- See the [API Reference](api_reference.md) for programmatic usage
- Visit the [Troubleshooting Guide](troubleshooting.md) if you encounter issues
