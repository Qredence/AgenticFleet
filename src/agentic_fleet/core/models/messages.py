"""
Custom message types for the Agentic Fleet system.

This module provides custom message types that extend the base message types
from autogen_core.models with additional fields required by the system.
"""


from autogen_core.models import SystemMessage as BaseSystemMessage


class EnhancedSystemMessage(BaseSystemMessage):
    """
    Enhanced version of SystemMessage that includes a source field.

    This class extends the base SystemMessage from autogen_core.models
    to include a source field, which is required by some components
    in the system.
    """

    def __init__(self, content: str, source: str = "system"):
        """
        Initialize an enhanced system message.

        Args:
            content: The content of the message
            source: The source of the message (defaults to "system")
        """
        super().__init__(content=content)
        # Add source as a private attribute to avoid Pydantic validation
        object.__setattr__(self, "_source", source)

    @property
    def source(self) -> str:
        """
        Get the source of the message.

        Returns:
            The source of the message
        """
        return object.__getattribute__(self, "_source")
