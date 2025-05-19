"""Tests for the task manager module."""

from enum import Enum
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agentic_fleet.ui.task_manager import extract_and_add_plan_tasks, update_task_status


# Define TaskStatus enum locally since it's not available in chainlit.types
class TaskStatus(str, Enum):
    """Status of a task."""

    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# Patch the Chainlit context to avoid context-related errors
@pytest.fixture
def mock_chainlit_context():
    with patch("chainlit.context.context_var") as mock_context_var:
        mock_context = MagicMock()
        mock_context.session = True
        mock_context_var.get.return_value = mock_context
        yield mock_context


@pytest.mark.asyncio
async def test_extract_plan_tasks(mock_user_session, mock_chainlit_elements, mock_chainlit_context):
    """Test extracting tasks from a plan and adding them to a task list."""
    plan_text = """1. First step
    2. Second step
    - Bullet point
    * Another item"""

    task_list = MagicMock()
    task_list.add_task = AsyncMock()

    # Create mock Text objects
    planning_mock = mock_chainlit_elements["text"]
    overview_mock = mock_chainlit_elements["text"]

    task_status = {"planning": planning_mock, "overview": overview_mock}

    with patch("chainlit.TaskList", return_value=task_list):
        await extract_and_add_plan_tasks(plan_text, task_list, task_status, "test_message", False)

    # Check that add_task was called for each extracted task
    assert task_list.add_task.call_count == 4

    # Check that send was called on both mock Text objects


@pytest.mark.asyncio
async def test_extract_plan_tasks_with_update(
    mock_user_session, mock_chainlit_elements, mock_chainlit_context
):
    """Test extracting tasks with the update flag set to True."""
    plan_text = "Updated plan with a single task"

    task_list = MagicMock()
    task_list.add_task = AsyncMock()

    # Create mock Text objects
    planning_mock = mock_chainlit_elements["text"]
    overview_mock = mock_chainlit_elements["text"]

    task_status = {"planning": planning_mock, "overview": overview_mock}

    with patch("chainlit.TaskList", return_value=task_list):
        await extract_and_add_plan_tasks(plan_text, task_list, task_status, "test_message", True)

    # Check that add_task was called for each extracted task
    assert task_list.add_task.call_count == 1


@pytest.mark.asyncio
async def test_update_task_status(mock_user_session, mock_chainlit_elements, mock_chainlit_context):
    """Test updating task status."""
    # Create a mock task
    mock_task = MagicMock()
    mock_task.id = "task_123"
    mock_task.status = TaskStatus.READY

    # Set up mock tasks in user session
    mock_user_session["plan_tasks"] = {"task_123": mock_task}

    # Create mock TaskList
    task_list = MagicMock()
    task_list.send = AsyncMock()

    with (
        patch("chainlit.TaskList", return_value=task_list),
        patch("chainlit.user_session", mock_user_session),
    ):
        await update_task_status("task_123", TaskStatus.RUNNING, "Working on task")

    # Verify task status was updated
    assert mock_task.status == TaskStatus.RUNNING


@pytest.mark.asyncio
async def test_update_task_status_nonexistent_task(
    mock_user_session, mock_chainlit_elements, mock_chainlit_context
):
    """Test updating a task that doesn't exist."""
    # Set up mock tasks in user session
    mock_user_session["plan_tasks"] = {}

    # Create mock TaskList
    task_list = MagicMock()
    task_list.send = AsyncMock()

    with (
        patch("chainlit.TaskList", return_value=task_list),
        patch("chainlit.user_session", mock_user_session),
    ):
        # Should not raise an exception
        await update_task_status("nonexistent_task", TaskStatus.RUNNING)
