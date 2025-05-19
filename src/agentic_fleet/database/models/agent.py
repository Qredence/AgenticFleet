"""
Agent database model.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from agentic_fleet.database.base import Base


class Agent(Base):
    """
    Agent database model.

    Represents an AI agent in the system.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    model = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="agent")
    messages = relationship("Message", back_populates="agent")

    def __repr__(self) -> str:
        """
        String representation of the Agent.
        """
        return f"<Agent {self.name}>"
