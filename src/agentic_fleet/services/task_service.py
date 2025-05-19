"""
Service for task management.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from agentic_fleet.schemas.task import Task, TaskCreate, TaskStatus, TaskUpdate

# Initialize logging
logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks."""

    def __init__(self):
        """Initialize the task service."""
        # In a real implementation, this would connect to a database
        # For now, we'll use an in-memory store
        self._tasks: dict[str, dict[str, Any]] = {}

    async def create_task(self, task: TaskCreate) -> Task:
        """
        Create a new task.

        Args:
            task: The task data to create

        Returns:
            The created task
        """
        try:
            task_id = f"task_{uuid4().hex}"
            now = datetime.now()

            task_data = {
                "id": task_id,
                "title": task.title,
                "description": task.description,
                "assigned_agent": task.assigned_agent,
                "status": TaskStatus.PENDING,
                "priority": task.priority,
                "deadline": task.deadline,
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
                "metadata": task.metadata,
                "results": None,
            }

            self._tasks[task_id] = task_data

            return Task(**task_data)
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise

    async def get_task(self, task_id: str) -> Task | None:
        """
        Get a task by ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The task if found, None otherwise
        """
        try:
            task_data = self._tasks.get(task_id)
            if not task_data:
                return None

            return Task(**task_data)
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            raise

    async def update_task(self, task_id: str, task: TaskUpdate) -> Task | None:
        """
        Update an existing task.

        Args:
            task_id: The ID of the task to update
            task: The updated task data

        Returns:
            The updated task if found, None otherwise
        """
        try:
            task_data = self._tasks.get(task_id)
            if not task_data:
                return None

            # Update only the fields that are provided
            update_data = task.dict(exclude_unset=True)

            for key, value in update_data.items():
                if value is not None:
                    task_data[key] = value

            task_data["updated_at"] = datetime.now()

            # If the task is being marked as completed, set the completed_at timestamp
            if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
                task_data["completed_at"] = datetime.now()

            self._tasks[task_id] = task_data

            return Task(**task_data)
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            raise

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: The ID of the task to delete

        Returns:
            True if the task was deleted, False otherwise
        """
        try:
            if task_id not in self._tasks:
                return False

            del self._tasks[task_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {str(e)}")
            raise

    async def list_tasks(self) -> list[Task]:
        """
        List all tasks.

        Returns:
            A list of all tasks
        """
        try:
            return [Task(**task_data) for task_data in self._tasks.values()]
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            raise

    async def assign_task(self, task_id: str, agent_id: str) -> Task | None:
        """
        Assign a task to an agent.

        Args:
            task_id: The ID of the task to assign
            agent_id: The ID of the agent to assign the task to

        Returns:
            The updated task if found, None otherwise
        """
        try:
            task_data = self._tasks.get(task_id)
            if not task_data:
                return None

            task_data["assigned_agent"] = agent_id
            task_data["updated_at"] = datetime.now()

            self._tasks[task_id] = task_data

            return Task(**task_data)
        except Exception as e:
            logger.error(f"Error assigning task {task_id} to agent {agent_id}: {str(e)}")
            raise
