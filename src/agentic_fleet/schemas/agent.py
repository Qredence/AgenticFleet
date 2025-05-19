"""
Pydantic schemas for agent-related data.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Base schema for agent data."""

    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent's capabilities")
    capabilities: list[str] = Field(default_factory=list, description="List of agent capabilities")


class AgentCreate(AgentBase):
    """Schema for creating a new agent."""

    model: str = Field(..., description="The model used by the agent")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Model parameters")


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""

    name: str | None = Field(None, description="Name of the agent")
    description: str | None = Field(None, description="Description of the agent's capabilities")
    capabilities: list[str] | None = Field(None, description="List of agent capabilities")
    model: str | None = Field(None, description="The model used by the agent")
    parameters: dict[str, Any] | None = Field(None, description="Model parameters")


class Agent(AgentBase):
    """Complete agent schema with all fields."""

    id: str = Field(..., description="Unique identifier for the agent")
    model: str = Field(..., description="The model used by the agent")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    created_at: datetime = Field(..., description="When the agent was created")
    updated_at: datetime = Field(..., description="When the agent was last updated")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
