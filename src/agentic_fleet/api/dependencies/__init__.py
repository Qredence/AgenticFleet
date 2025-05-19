"""
Dependencies package for the Agentic Fleet API.

This package contains dependency injection components for FastAPI.
"""

from agentic_fleet.api.dependencies.services import (
    get_agent_service,
    get_chat_service,
    get_task_service,
)

__all__ = ["get_agent_service", "get_task_service", "get_chat_service"]
