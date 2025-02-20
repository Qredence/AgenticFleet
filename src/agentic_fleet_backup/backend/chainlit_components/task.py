"""Task component for AgenticFleet."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """A task in a task list."""

    title: str
    status: str = field(default="ready")
    output: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert task to dictionary.

        Returns:
            dict: Dictionary representation of task
        """
        return {
            "title": self.title,
            "status": self.status,
            "output": self.output,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary.

        Args:
            data: Dictionary representation of task

        Returns:
            Task: Created task
        """
        return cls(
            title=data["title"],
            status=data.get("status", "ready"),
            output=data.get("output"),
            error=data.get("error"),
        )
