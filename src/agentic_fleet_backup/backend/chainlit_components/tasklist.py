"""TaskList component for AgenticFleet."""

from enum import Enum
from typing import List, Optional

import chainlit as cl


class TaskStatus(Enum):
    """Task status enum."""
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Task:
    """A task in a task list."""

    def __init__(
        self,
        title: str,
        status: TaskStatus = TaskStatus.READY,
        for_id: Optional[str] = None
    ):
        """Initialize task.

        Args:
            title: Task title
            status: Task status
            for_id: Optional message ID to link to
        """
        self.title = title
        self.status = status
        self.for_id = for_id


class TaskList:
    """A list of tasks with UI synchronization."""

    def __init__(self):
        """Initialize task list."""
        self.tasks: List[Task] = []
        self.status: str = "Ready"

    async def add_task(self, task: Task) -> None:
        """Add a task to the list.

        Args:
            task: Task to add
        """
        self.tasks.append(task)
        await self.send()

    async def remove_task(self, task: Task) -> None:
        """Remove a task from the list.

        Args:
            task: Task to remove
        """
        if task in self.tasks:
            self.tasks.remove(task)
            await self.send()

    async def clear(self) -> None:
        """Clear all tasks from the list."""
        self.tasks.clear()
        await self.send()

    async def send(self) -> None:
        """Send task list update to UI."""
        task_elements = []
        for task in self.tasks:
            task_element = {
                "type": "task",
                "title": task.title,
                "status": task.status.value,
            }
            if task.for_id:
                task_element["forId"] = task.for_id
            task_elements.append(task_element)

        await cl.Message(
            content="",
            elements=task_elements,
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
