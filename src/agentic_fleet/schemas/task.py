"""
Pydantic schemas for task-related data.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Enum for task status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskBase(BaseModel):
    """Base schema for task data."""

    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    assigned_agent: str | None = Field(None, description="ID of the agent assigned to the task")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    priority: int = Field(default=1, description="Priority level (1-5)")
    deadline: datetime | None = Field(None, description="When the task should be completed by")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: str | None = Field(None, description="Title of the task")
    description: str | None = Field(None, description="Detailed description of the task")
    status: TaskStatus | None = Field(None, description="Current status of the task")
    assigned_agent: str | None = Field(None, description="ID of the agent assigned to the task")
    priority: int | None = Field(None, description="Priority level (1-5)")
    deadline: datetime | None = Field(None, description="When the task should be completed by")
    metadata: dict[str, Any] | None = Field(None, description="Additional task metadata")
    results: Any | None = Field(None, description="Task results")


class Task(TaskBase):
    """Complete task schema with all fields."""

    id: str = Field(..., description="Unique identifier for the task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    priority: int = Field(default=1, description="Priority level (1-5)")
    deadline: datetime | None = Field(None, description="When the task should be completed by")
    created_at: datetime = Field(..., description="When the task was created")
    updated_at: datetime = Field(..., description="When the task was last updated")
    completed_at: datetime | None = Field(None, description="When the task was completed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")
    results: Any | None = Field(None, description="Task results")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
