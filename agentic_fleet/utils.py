import logging
import os

from agentic_fleet.config import config_manager

logger = logging.getLogger(__name__)


def cleanup_workspace():
    """Cleanup workspace by removing the workspace directory if it exists."""
    try:
        env_config = config_manager.get_environment_settings()
        workspace_dir = os.path.join(os.getcwd(), env_config.get("workspace_dir", "workspace"))
        if os.path.exists(workspace_dir):
            import shutil
            shutil.rmtree(workspace_dir)
            logger.info("Workspace cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to clean up workspace: {e}")


def create_and_set_workspace(user_profile):
    """Create and set a new workspace for the user. This is a stub implementation."""
    workspace = os.path.join(os.getcwd(), "workspace")
    logger.info(f"Workspace created for user: {user_profile.get('name', 'unknown')}, at {workspace}")
    # You might want to add more logic here to create the directory and update user_profile
    user_profile["workspace"] = workspace
    return workspace


def get_user_profile():
    """Return a dummy user profile."""
    # In a real application, retrieve the user profile from your authentication system
    return {"name": "default_user"}


def load_settings():
    """Load settings for the chat session. Stub implementation returning default settings."""
    return {
        "start_page": "https://www.bing.com",
        "max_rounds": 10,
        "max_time": 300,
        "max_stalls": 3
    }


def save_settings(settings):
    """Save settings. Stub implementation that logs the settings."""
    logger.info(f"Settings saved: {settings}")


async def setup_chat_settings():
    """Setup chat settings. Stub implementation."""
    logger.info("Chat settings setup invoked.")


def update_task_status(status, message):
    """Update task status. Stub implementation."""
    logger.info(f"Task status updated to {status} with message: {message}")


def get_task_status():
    """Get task status. Stub implementation."""
    return "completed"

