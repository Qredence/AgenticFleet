"""Core module for AgenticFleet application.

This module contains core application functionality including:
- Application configuration and startup
- Core agent components and interfaces
- Base classes and utilities
"""

from .application import ApplicationManager, create_application

__all__ = [
    'ApplicationManager',
    'create_application',
]