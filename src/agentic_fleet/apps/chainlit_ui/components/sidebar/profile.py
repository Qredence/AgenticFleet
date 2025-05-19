"""Profile component for the Chainlit UI sidebar."""

from typing import Any

import chainlit as cl


class ProfileSettings:
    """A component for managing user profile settings."""

    def __init__(self, user_id: str, settings: dict[str, Any] | None = None):
        """Initialize profile settings.

        Args:
            user_id: The user's identifier
            settings: Optional user settings
        """
        self.user_id = user_id
        self.settings = settings or {}

    async def render(self) -> None:
        """Render the profile settings in the sidebar."""
        with cl.sidebar():
            await cl.Text(name="user_id", label="User ID", value=self.user_id).send()

            for key, value in self.settings.items():
                await cl.Text(
                    name=key, label=key.replace("_", " ").title(), value=str(value)
                ).send()
