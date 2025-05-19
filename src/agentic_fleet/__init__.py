"""
AgenticFleet - A multi-agent system for adaptive AI reasoning and automation.

This package provides a powerful framework for building and deploying multi-agent systems
that can adapt and reason about complex tasks. It integrates with FastAPI for the backend
and provides a modern web interface for interaction.

The system features a clean, modular architecture with:
- A unified configuration system
- A flexible agent registry
- A robust API layer
- Multiple UI options including Chainlit
"""

__version__ = "0.5.0"
__author__ = "Qredence"
__email__ = "contact@qredence.ai"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2025 Qredence"

from importlib.metadata import PackageNotFoundError, version

from agentic_fleet.config import config_manager

try:
    __version__ = version("agentic-fleet")
except PackageNotFoundError:
    # Package is not installed
    pass

# Initialize configuration
config_manager.load_all()

__all__ = [
    # Configuration
    "config_manager",
]
