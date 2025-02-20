"""TaskList component for AgenticFleet."""

import asyncio
from typing import List, Optional

import chainlit as cl

from agentic_fleet.backend.chainlit_components.task import Task


class TaskList:
    """A list of tasks with UI synchronization."""

    def __init__(self):
        """Initialize task list."""
        self.tasks: List[Task] = []
        self.status: str = "Ready"
        self._lock = asyncio.Lock()

    async def add_task(self, task: Task) -> None:
        """Add a task to the list.

        Args:
            task: Task to add
        """
        async with self._lock:
            self.tasks.append(task)
            await self.send()

    async def remove_task(self, task: Task) -> None:
        """Remove a task from the list.

        Args:
            task: Task to remove
        """
        async with self._lock:
            if task in self.tasks:
                self.tasks.remove(task)
                await self.send()

    async def clear(self) -> None:
        """Clear all tasks from the list."""
        async with self._lock:
            self.tasks.clear()
            await self.send()

    async def send(self) -> None:
        """Send task list update to UI."""
        elements = [
            {
                "type": "task",
                "title": task.title,
                "status": task.status,
                "output": task.output,
                "error": task.error,
            }
            for task in self.tasks
        ]

        await cl.Message(
            content="",
            elements=elements,
            author="Task Manager",
            metadata={"status": self.status},
        ).send()

    async def remove(self) -> None:
        """Remove task list from UI."""
        await self.clear()
        self.status = "Removed"
        await self.send()

    def get_task_by_title(self, title: str) -> Optional[Task]:
        """Get task by title.

        Args:
            title: Task title to find

        Returns:
            Task if found, None otherwise
        """
        for task in self.tasks:
            if task.title == title:
                return task
        return None

    def to_dict(self) -> dict:
        """Convert task list to dictionary.

        Returns:
            dict: Dictionary representation of task list
        """
        return {
            "tasks": [task.to_dict() for task in self.tasks],
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskList":
        """Create task list from dictionary.

        Args:
            data: Dictionary representation of task list

        Returns:
            TaskList: Created task list
        """
        task_list = cls()
        task_list.tasks = [Task.from_dict(task_data) for task_data in data["tasks"]]
        task_list.status = data["status"]
        return task_list
