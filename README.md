# AgenticFleet

A multi-agent system for adaptive AI reasoning and automation.

## Overview

AgenticFleet is a modular framework for building, orchestrating, and deploying multi-agent AI systems. It integrates:

- **Chainlit** for a modern, interactive web UI
- **FastAPI** for robust backend APIs
- **Flexible agent registry** for custom teams and workflows
- **Unified configuration system** for easy environment and model management

## Features

- 🤖 Multiple specialized agents (web, file, code, execution)
- 🌐 Web search and information gathering
- 📁 File operations and management
- 💻 Code generation and execution
- 🚀 Real-time streaming responses
- 📊 Task progress tracking
- 🔄 Automatic resource cleanup

## Quick Start

### Prerequisites

- Python 3.10+
- Azure OpenAI API access (or compatible LLM provider)
- [Node.js](https://nodejs.org/) (optional, for frontend development)

### Installation

```bash
# Clone the repository
 git clone <your-repo-url>
 cd AgenticFleet

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS

# Install dependencies
pip install -r requirements.txt

# (Optional) Install browser automation dependencies
playwright install chromium
```

### Configuration

1. Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:
   ```env
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_API_VERSION=your_api_version
   ```
2. Adjust settings in `src/agentic_fleet/config/settings/app_settings.yaml` as needed.

### Running the Chainlit UI

```bash
python -m src.agentic_fleet.app
```

Or, using the CLI:

```bash
python -m src.agentic_fleet.cli start
```

The app will be available at [http://localhost:8000](http://localhost:8000).

### Running the FastAPI Backend (API only)

```bash
uvicorn src.agentic_fleet.api.app:app --reload
```

## Project Structure

```
AgenticFleet/
  src/agentic_fleet/
    chainlit_app.py      # Main Chainlit UI entry point
    api/app.py           # Main FastAPI app
    config/              # Unified configuration system
    services/            # Business logic services
    core/                # Core agent and orchestration logic
    ...
  tests/                 # Unit and integration tests
  requirements.txt       # Python dependencies
  Dockerfile             # Containerization support
  ...
```

## Contributing

Contributions are welcome! Please:

- Open issues for bugs or feature requests
- Submit pull requests with clear descriptions
- Follow the code style and commit guidelines

## License

This project is licensed under the Apache 2.0 License.

## Contact

For questions or support, contact [Qredence](mailto:contact@qredence.ai).
