"""Task management module for AgenticFleet."""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from agentic_fleet.backend.chainlit_components.task import Task
from agentic_fleet.backend.chainlit_components.task_list import TaskList


class TaskStatus(Enum):
    """Task status enum for task management."""
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskState(Enum):
    """Task states for the task manager."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskManager:
    """Manages task lists and their states."""

    def __init__(self):
        """Initialize the task manager."""
        self.task_list: Optional[TaskList] = None
        self.task_history: Dict[str, List[Dict]] = {}
        self._lock = asyncio.Lock()

    async def initialize_task_list(self) -> TaskList:
        """Initialize a new task list.

        Returns:
            TaskList: The newly created task list
        """
        async with self._lock:
            self.task_list = TaskList()
            self.task_list.status = "Ready"
            await self.task_list.send()
            return self.task_list

    async def add_task(self, title: str) -> Task:
        """Add a new task to the task list.

        Args:
            title: The title of the task

        Returns:
            Task: The newly created task

        Raises:
            RuntimeError: If task list is not initialized
        """
        if not self.task_list:
            raise RuntimeError("Task list not initialized")

        async with self._lock:
            task = Task(title=title)
            await self.task_list.add_task(task)
            await self.task_list.send()
            return task

    async def update_task_status(
        self, task: Task, status: TaskStatus, error: Optional[str] = None
    ) -> None:
        """Update the status of a task.

        Args:
            task: The task to update
            status: The new status
            error: Optional error message if task failed
        """
        if not self.task_list:
            raise RuntimeError("Task list not initialized")

        async with self._lock:
            task.status = status
            if error:
                task.title = f"{task.title} (Error: {error})"
            await self.task_list.send()

            # Record in history
            self.task_history.setdefault(task.title, []).append(
                {
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                }
            )

    async def set_list_status(self, status: str) -> None:
        """Set the status of the task list.

        Args:
            status: The new status

        Raises:
            RuntimeError: If task list is not initialized
        """
        if not self.task_list:
            raise RuntimeError("Task list not initialized")

        async with self._lock:
            self.task_list.status = status
            await self.task_list.send()

    async def clear_tasks(self) -> None:
        """Clear all tasks from the task list."""
        if not self.task_list:
            raise RuntimeError("Task list not initialized")

        async with self._lock:
            self.task_list.tasks.clear()
            await self.task_list.send()

    def get_task_history(self, task_title: str) -> List[Dict]:
        """Get the history of a specific task.

        Args:
            task_title: The title of the task

        Returns:
            List[Dict]: List of task history entries
        """
        return self.task_history.get(task_title, [])

    async def mark_running_tasks_as_failed(self, error: str = "Task interrupted") -> None:
        """Mark all running tasks as failed.

        Args:
            error: The error message to set
        """
        if not self.task_list:
            return

        async with self._lock:
            for task in self.task_list.tasks:
                if task.status == TaskStatus.RUNNING:
                    await self.update_task_status(task, TaskStatus.FAILED, error)
