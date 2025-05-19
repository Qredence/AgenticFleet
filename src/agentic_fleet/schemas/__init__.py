"""
Schemas package for the Agentic Fleet application.

This package contains all the Pydantic schemas used for data validation and serialization.
"""

from agentic_fleet.schemas.agent import Agent, AgentBase, AgentCreate, AgentUpdate
from agentic_fleet.schemas.message import (
    Message,
    MessageBase,
    MessageCreate,
    MessageType,
    MessageUpdate,
)
from agentic_fleet.schemas.task import Task, TaskBase, TaskCreate, TaskStatus, TaskUpdate

__all__ = [
    "Agent",
    "AgentCreate",
    "AgentUpdate",
    "AgentBase",
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskBase",
    "TaskStatus",
    "Message",
    "MessageCreate",
    "MessageUpdate",
    "MessageBase",
    "MessageType",
]
