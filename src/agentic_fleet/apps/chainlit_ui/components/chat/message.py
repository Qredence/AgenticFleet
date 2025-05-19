"""Chat message component for the Chainlit UI."""

from typing import Any

from chainlit.message import Message


class ChatMessage:
    """A component for rendering chat messages."""

    def __init__(self, content: str, author: str, metadata: dict[str, Any] | None = None):
        """Initialize a chat message.

        Args:
            content: The message content
            author: The message author
            metadata: Optional metadata for the message
        """
        self.content = content
        self.author = author
        self.metadata = metadata or {}

    async def send(self) -> Message:
        """Send the message to the UI.

        Returns:
            The sent message object
        """
        return await Message(
            content=self.content, author=self.author, metadata=self.metadata
        ).send()
