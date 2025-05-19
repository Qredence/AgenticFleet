"""
Task database model.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from agentic_fleet.database.base import Base


class TaskStatus(enum.Enum):
    """
    Task status enum.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    """
    Task database model.

    Represents a task assigned to an agent.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # Task configuration and results
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)

    # Foreign keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=False)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("task.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    messages = relationship("Message", back_populates="task")
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])

    def __repr__(self) -> str:
        """
        String representation of the Task.
        """
        return f"<Task {self.title} - {self.status.value}>"
