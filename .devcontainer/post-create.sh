#!/bin/bash
set -e

# Update system and install dependencies
sudo apt-get update
sudo apt-get install -y --no-install-recommends build-essential curl

# Upgrade pip
pip install --upgrade pip

# Check if src/requirements.txt exists, otherwise use root requirements.txt
if [ -f "src/requirements.txt" ]; then
    pip install -r src/requirements.txt
else
    # Install the project in development mode
    pip install -e ".[dev,test]"
fi

# Ensure agentic-fleet is installed
pip install agentic-fleet

# Install additional tools
pip install ruff mypy pre-commit

# Install playwright
pip install playwright
playwright install --with-deps chromium

# Install pre-commit hooks if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
fi

# Create necessary directories
mkdir -p ~/.config/shell && touch ~/.config/shell/bash_history

echo "Development environment setup complete!"
