"""Module for task management functions."""

# Standard library imports
import logging

# Third-party imports
import chainlit as cl
from chainlit import TaskList, TaskStatus, user_session

# Initialize logging
logger = logging.getLogger(__name__)


async def initialize_task_list():
    """Initialize and send the task list."""
    task_list = TaskList()
    task_list.status = "Ready"
    user_session.set("task_list", task_list)
    await task_list.send()
    return task_list


async def extract_and_add_plan_tasks(
    plan_text: str,
    task_list: cl.TaskList | None = None,
    task_status: dict[str, cl.Text] | None = None,
    message_id: str | None = None,
    is_update: bool = False,
):
    """Extract plan steps and add them as individual tasks to the TaskList.

    Args:
        plan_text: The plan text to extract steps from
        task_list: Optional TaskList instance. If not provided, will be fetched from user session
        task_status: Dictionary of Text elements for status updates
        message_id: ID of the message to associate status updates with
        is_update: Whether this is an update to an existing plan
    """
    # Added input validation
    if not isinstance(plan_text, str) or len(plan_text.strip()) == 0:
        logger.error("Invalid plan text provided")
        return

    # Get task list from session if not provided
    if task_list is None:
        try:
            task_list = cl.user_session.get("task_list")
        except Exception:
            logger.warning("Could not retrieve task list from user session")
            return

    # Safely get plan steps, defaulting to an empty dict
    try:
        plan_steps = cl.user_session.get("plan_steps", {}) or {}
    except Exception:
        plan_steps = {}

    # Extract tasks from plan text
    tasks = []
    for line in plan_text.split("\n"):
        line = line.strip()
        # More flexible task extraction
        if line and (
            any(line.startswith(prefix) for prefix in ["1.", "2.", "3.", "-", "*"])
            or len(line.split()) > 2  # Capture lines with more than 2 words
        ):
            task_id = f"task_{len(tasks) + 1}"
            task = {"id": task_id, "title": line, "status": cl.TaskStatus.READY}
            tasks.append(task)

    # Add tasks to task list only if task_list is valid
    if task_list:
        for task in tasks:
            # Remove id parameter from constructor
            task_obj = cl.Task(
                title=task["title"],
                status=task["status"],
                # id=task["id"] # Removed based on Pylance error
            )
            # Store the intended ID separately if needed for tracking
            # task_obj.id = task["id"] # Or manage IDs in plan_steps dict
            await task_list.add_task(task_obj)
    else:
        logger.error("Task list not found in session, cannot add tasks.")

    # Update plan steps in user session
    try:
        if is_update:
            # If updating, preserve existing steps and add new tasks
            for task in tasks:
                plan_steps[task["id"]] = task
        else:
            # If not updating, clear existing steps and add new tasks
            plan_steps.clear()
            for task in tasks:
                plan_steps[task["id"]] = task

        cl.user_session.set("plan_steps", plan_steps)
    except Exception as e:
        logger.warning(f"Could not update plan steps in user session: {e}")

    # Update task status text if provided
    if task_status and "planning" in task_status and message_id:
        try:
            # Add for_id back as required by linter here
            await task_status["planning"].send(for_id=message_id)
        except Exception as e:
            logger.warning(f"Could not send planning status: {e}")

    # Log task addition
    logger.info(f"Added {len(tasks)} tasks to the task list")


async def update_task_status(task_id: str, status: TaskStatus, message: str | None = None):
    """Update the status of a task in the task list.

    Args:
        task_id: The ID of the task to update
        status: The new status for the task
        message: Optional message to display with the status update
    """
    # Safely get plan tasks
    try:
        # Ensure plan_tasks is retrieved as a dict, default to empty dict if None or error
        plan_tasks = cl.user_session.get("plan_tasks") or {}
        if not isinstance(plan_tasks, dict):
            logger.warning(
                f"plan_tasks retrieved from session is not a dict: {type(plan_tasks)}. Resetting."
            )
            plan_tasks = {}

    except Exception as e:
        plan_tasks = {}  # Default to empty dict on error
        logger.warning(f"Could not access user session for plan_tasks: {e}")

    # Check if task_id exists in the plan_tasks dictionary
    if isinstance(plan_tasks, dict) and task_id in plan_tasks:
        task = plan_tasks.get(task_id)  # Use .get for safer access

        # Ensure task is not None before accessing attributes
        if task:
            # Ensure task is an object with status attribute (could be dict from session)
            if hasattr(task, "status"):
                task.status = status

            # Update task title with message if provided
            if hasattr(task, "title"):
                if message and status == TaskStatus.DONE:
                    task.title = f"{task.title} ✓ {message}"
                elif message and status == TaskStatus.FAILED:
                    task.title = f"{task.title} ❌ {message}"

            # Update the task data within the plan_tasks dictionary
            if isinstance(task, dict):  # If task is stored as dict
                task["status"] = status
                if message and status == TaskStatus.DONE:
                    task["title"] = f"{task.get('title', '')} ✓ {message}"
                elif message and status == TaskStatus.FAILED:
                    task["title"] = f"{task.get('title', '')} ❌ {message}"
            elif hasattr(task, "status"):  # If task is stored as object
                task.status = status
                if hasattr(task, "title"):
                    if message and status == TaskStatus.DONE:
                        task.title = f"{task.title} ✓ {message}"
                    elif message and status == TaskStatus.FAILED:
                        task.title = f"{task.title} ❌ {message}"

            # Update the plan_tasks dictionary in the session (only if task was found)
            try:
                cl.user_session.set("plan_tasks", plan_tasks)
            except Exception as e:
                logger.warning(f"Could not update plan_tasks in user session: {e}")

            # Get the task list from the session and send update (only if task was found)
            try:
                task_list = cl.user_session.get("task_list")
                if task_list and hasattr(task_list, "send"):
                    # Re-send the entire task list to reflect updates
                    await task_list.send()
                else:
                    logger.warning("Could not retrieve task_list from session to send update.")
            except Exception as e:
                logger.warning(f"Could not send task list update: {e}")

            logger.info(f"Updated task {task_id} status to {status}")
        else:
            # Log if task was None
            logger.warning(f"Task object for ID {task_id} is None or invalid.")

    elif not isinstance(plan_tasks, dict):
        logger.error(f"plan_tasks is not a dictionary, cannot update task {task_id}")
    else:
        # Only log warning if plan_tasks is confirmed to be a dict and task_id not found
        if isinstance(plan_tasks, dict):
            logger.warning(f"Task ID {task_id} not found in plan_tasks dictionary.")
