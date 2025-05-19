"""
Message database model.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from agentic_fleet.database.base import Base


class Message(Base):
    """
    Message database model.

    Represents a message in a conversation.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system, etc.
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Optional metadata
    message_metadata = Column(JSON, nullable=True)

    # Foreign keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("task.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="messages")
    task = relationship("Task", back_populates="messages")

    def __repr__(self) -> str:
        """
        String representation of the Message.
        """
        return f"<Message {self.id} - {self.role}>"
