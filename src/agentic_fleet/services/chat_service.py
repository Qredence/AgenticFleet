"""
Service for chat functionality.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

from agentic_fleet.schemas.message import Message, MessageCreate, MessageType, MessageUpdate

# Initialize logging
logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat functionality."""

    def __init__(self):
        """Initialize the chat service."""
        # In a real implementation, this would connect to a database
        # For now, we'll use in-memory stores
        self._messages: dict[str, dict[str, Any]] = {}
        # session_id -> list of message_ids
        self._sessions: dict[str, list[str]] = {}
        # session_id -> WebSocket
        self._active_connections: dict[str, WebSocket] = {}

    async def process_message(self, message: MessageCreate) -> Message:
        """
        Process an incoming message.

        Args:
            message: The message data to process

        Returns:
            The processed message
        """
        try:
            message_id = f"msg_{uuid4().hex}"
            now = datetime.now()

            # Create the message
            message_data = {
                "id": message_id,
                "content": message.content,
                "sender": message.sender,
                "receiver": message.receiver,
                "message_type": message.message_type,
                "session_id": message.session_id,
                "parent_id": message.parent_id,
                "timestamp": now,
                "edited_at": None,
                "is_edited": False,
                "metadata": message.metadata,
                "attachments": message.attachments,
            }

            # Store the message
            self._messages[message_id] = message_data

            # Add to session
            if message.session_id not in self._sessions:
                self._sessions[message.session_id] = []
            self._sessions[message.session_id].append(message_id)

            # Create the response message
            return Message(**message_data)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    async def get_message(self, message_id: str) -> Message | None:
        """
        Get a message by ID.

        Args:
            message_id: The ID of the message to retrieve

        Returns:
            The message if found, None otherwise
        """
        try:
            message_data = self._messages.get(message_id)
            if not message_data:
                return None

            return Message(**message_data)
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {str(e)}")
            raise

    async def update_message(self, message_id: str, message: MessageUpdate) -> Message | None:
        """
        Update an existing message.

        Args:
            message_id: The ID of the message to update
            message: The updated message data

        Returns:
            The updated message if found, None otherwise
        """
        try:
            message_data = self._messages.get(message_id)
            if not message_data:
                return None

            # Update only the fields that are provided
            update_data = message.dict(exclude_unset=True)

            for key, value in update_data.items():
                if value is not None:
                    message_data[key] = value

            message_data["edited_at"] = datetime.now()
            message_data["is_edited"] = True

            self._messages[message_id] = message_data

            return Message(**message_data)
        except Exception as e:
            logger.error(f"Error updating message {message_id}: {str(e)}")
            raise

    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.

        Args:
            message_id: The ID of the message to delete

        Returns:
            True if the message was deleted, False otherwise
        """
        try:
            if message_id not in self._messages:
                return False

            message_data = self._messages[message_id]
            session_id = message_data["session_id"]

            # Remove from session
            if session_id in self._sessions and message_id in self._sessions[session_id]:
                self._sessions[session_id].remove(message_id)

            # Delete the message
            del self._messages[message_id]

            return True
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {str(e)}")
            raise

    async def get_chat_history(self, session_id: str) -> list[Message]:
        """
        Get chat history for a session.

        Args:
            session_id: The ID of the session to get history for

        Returns:
            A list of messages in the session
        """
        try:
            if session_id not in self._sessions:
                return []

            message_ids = self._sessions[session_id]
            messages = []

            for message_id in message_ids:
                if message_id in self._messages:
                    messages.append(Message(**self._messages[message_id]))

            # Sort by timestamp
            messages.sort(key=lambda m: m.timestamp)

            return messages
        except Exception as e:
            logger.error(f"Error getting chat history for session {session_id}: {str(e)}")
            raise

    async def register_websocket(self, session_id: str, websocket: WebSocket) -> None:
        """
        Register a WebSocket connection for a session.

        Args:
            session_id: The ID of the session
            websocket: The WebSocket connection
        """
        try:
            self._active_connections[session_id] = websocket
            logger.info(f"Registered WebSocket for session {session_id}")
        except Exception as e:
            logger.error(f"Error registering WebSocket for session {session_id}: {str(e)}")
            raise

    async def unregister_websocket(self, session_id: str) -> None:
        """
        Unregister a WebSocket connection for a session.

        Args:
            session_id: The ID of the session
        """
        try:
            if session_id in self._active_connections:
                del self._active_connections[session_id]
                logger.info(f"Unregistered WebSocket for session {session_id}")
        except Exception as e:
            logger.error(f"Error unregistering WebSocket for session {session_id}: {str(e)}")
            raise

    async def process_websocket_message(self, session_id: str, data: dict[str, Any]) -> Message:
        """
        Process a message received via WebSocket.

        Args:
            session_id: The ID of the session
            data: The message data

        Returns:
            The processed message
        """
        try:
            # Create a MessageCreate object from the data
            message_data = {
                "content": data.get("content", ""),
                "sender": data.get("sender", "user"),
                "receiver": data.get("receiver", "assistant"),
                "message_type": data.get("message_type", MessageType.TEXT),
                "session_id": session_id,
                "parent_id": data.get("parent_id"),
                "metadata": data.get("metadata", {}),
                "attachments": data.get("attachments", []),
            }

            message = MessageCreate(**message_data)

            # Process the message
            return await self.process_message(message)
        except Exception as e:
            logger.error(f"Error processing WebSocket message for session {session_id}: {str(e)}")
            raise

    async def broadcast_message(self, message: Message) -> None:
        """
        Broadcast a message to all connected clients for the session.

        Args:
            message: The message to broadcast
        """
        try:
            session_id = message.session_id
            if session_id in self._active_connections:
                websocket = self._active_connections[session_id]
                await websocket.send_json(message.dict())
                logger.info(f"Broadcasted message {message.id} to session {session_id}")
        except Exception as e:
            logger.error(f"Error broadcasting message {message.id}: {str(e)}")
            raise
