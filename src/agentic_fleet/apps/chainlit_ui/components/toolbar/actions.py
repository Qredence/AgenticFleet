"""Actions component for the Chainlit UI toolbar."""

from collections.abc import Callable

import chainlit as cl


class ToolbarActions:
    """A component for managing toolbar actions."""

    def __init__(self):
        """Initialize toolbar actions."""
        self.actions: dict[str, Callable] = {}

    def add_action(self, name: str, callback: Callable) -> None:
        """Add an action to the toolbar.

        Args:
            name: The name of the action
            callback: The callback function to execute
        """
        self.actions[name] = callback

    async def render(self) -> None:
        """Render the actions in the toolbar."""
        for name, callback in self.actions.items():
            await cl.Action(
                name=name,
                label=name.replace("_", " ").title(),
                description=f"Execute {name} action",
                callback=callback,
            ).send()

    @classmethod
    async def create_default(cls) -> "ToolbarActions":
        """Create a toolbar with default actions.

        Returns:
            A ToolbarActions instance with default actions
        """
        toolbar = cls()

        async def clear_chat():
            await cl.Message(content="Chat cleared").send()

        async def export_chat():
            await cl.Message(content="Chat exported").send()

        toolbar.add_action("clear_chat", clear_chat)
        toolbar.add_action("export_chat", export_chat)

        return toolbar
