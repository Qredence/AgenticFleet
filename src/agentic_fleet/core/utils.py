import logging
import os
import socket
import subprocess

import psutil

logger = logging.getLogger(__name__)


def cleanup_workspace():
    """Cleanup workspace by removing the workspace directory if it exists."""
    from agentic_fleet.config import config_manager

    try:
        env_config = config_manager.get_environment_settings()
        workspace_dir = os.path.join(os.getcwd(), getattr(env_config, "workspace_dir", "workspace"))
        if os.path.exists(workspace_dir):
            import shutil

            shutil.rmtree(workspace_dir)
            logger.info("Workspace cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to clean up workspace: {e}")


def create_and_set_workspace(user_profile):
    """Create and set a new workspace for the user. This is a stub implementation."""
    workspace = os.path.join(os.getcwd(), "workspace")
    logger.info(
        f"Workspace created for user: {user_profile.get('name', 'unknown')}, at {workspace}"
    )
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
        "max_stalls": 3,
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


def check_port_availability(host: str, port: int) -> bool:
    """Check if a port is available on the given host.

    Args:
        host: Host address to check
        port: Port number to check

    Returns:
        bool: True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 8000, max_attempts: int = 3) -> int | None:
    """Find an available port starting from start_port.

    Args:
        start_port: Port number to start checking from
        max_attempts: Maximum number of ports to check

    Returns:
        Optional[int]: Available port number or None if no port found
    """
    for port in range(start_port, start_port + max_attempts):
        if check_port_availability("localhost", port):
            return port
    return None


def get_running_instance() -> tuple[int, int] | None:
    """Check if an AgenticFleet instance is already running.

    Returns:
        Optional[Tuple[int, int]]: Tuple of (pid, port) if running, None otherwise
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if "agenticfleet" in " ".join(proc.info["cmdline"] or []):
                # Extract port from command line arguments
                cmdline = proc.info["cmdline"]
                if "--port" in cmdline:
                    port_idx = cmdline.index("--port") + 1
                    if port_idx < len(cmdline):
                        return (proc.info["pid"], int(cmdline[port_idx]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def cleanup_running_instances() -> None:
    """Cleanup any running AgenticFleet instances."""
    try:
        # Find and terminate Python processes running AgenticFleet
        subprocess.run(["pkill", "-f", "agenticfleet"], check=False)
    except Exception as e:
        logger.error(f"Failed to cleanup running instances: {e}")


def ensure_directory_exists(path: str) -> None:
    """
    Ensure that a directory exists. If it does not, create it (including parents).
    Args:
        path: The directory path to ensure exists.
    """
    from pathlib import Path

    logger = logging.getLogger(__name__)
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
