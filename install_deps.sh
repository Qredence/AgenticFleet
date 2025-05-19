#!/bin/bash
# Script to install dependencies for the Agentic Fleet project

# Ensure we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please activate a virtual environment first."
    echo "Example: python -m venv venv && source venv/bin/activate"
    exit 1
fi

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing the package in development mode..."
pip install -e ".[dev]"

echo "Dependencies installed successfully!"
echo "You can now run the application with: python -m agentic_fleet.main"
echo "Or use the entry point: agentic-fleet"
