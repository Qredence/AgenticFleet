"""
Pydantic schemas for message-related data.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enum for message types."""

    TEXT = "text"
    IMAGE = "image"
    CODE = "code"
    FILE = "file"
    SYSTEM = "system"


class MessageBase(BaseModel):
    """Base schema for message data."""

    content: str = Field(..., description="Content of the message")
    sender: str = Field(..., description="ID or name of the sender")
    receiver: str = Field(..., description="ID or name of the receiver")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    session_id: str = Field(..., description="ID of the chat session")
    parent_id: str | None = Field(None, description="ID of the parent message (for threading)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata"
    )
    attachments: list[dict[str, Any]] = Field(
        default_factory=list, description="Attached files or media"
    )


class MessageUpdate(BaseModel):
    """Schema for updating an existing message."""

    content: str | None = Field(None, description="Content of the message")
    metadata: dict[str, Any] | None = Field(None, description="Additional message metadata")
    is_edited: bool | None = Field(None, description="Whether the message has been edited")


class Message(MessageBase):
    """Complete message schema with all fields."""

    id: str = Field(..., description="Unique identifier for the message")
    session_id: str = Field(..., description="ID of the chat session")
    parent_id: str | None = Field(None, description="ID of the parent message (for threading)")
    timestamp: datetime = Field(..., description="When the message was sent")
    edited_at: datetime | None = Field(None, description="When the message was last edited")
    is_edited: bool = Field(default=False, description="Whether the message has been edited")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata"
    )
    attachments: list[dict[str, Any]] = Field(
        default_factory=list, description="Attached files or media"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True
