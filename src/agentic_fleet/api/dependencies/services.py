"""
Dependencies for service injection.
"""

from functools import lru_cache

from agentic_fleet.services.agent_service import AgentService
from agentic_fleet.services.chat_service import ChatService
from agentic_fleet.services.task_service import TaskService


@lru_cache
def get_agent_service() -> AgentService:
    """
    Get the agent service singleton.

    Returns:
        The agent service instance
    """
    return AgentService()


@lru_cache
def get_task_service() -> TaskService:
    """
    Get the task service singleton.

    Returns:
        The task service instance
    """
    return TaskService()


@lru_cache
def get_chat_service() -> ChatService:
    """
    Get the chat service singleton.

    Returns:
        The chat service instance
    """
    return ChatService()
