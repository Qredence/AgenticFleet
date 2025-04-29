"""
Chainlit application entry point for AgenticFleet.

This module serves as the primary entry point for the Chainlit UI application.
"""

# Initialize environment variables first
from dotenv import load_dotenv

# Third-party imports
# Standard library imports
import asyncio
import logging
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import chainlit as cl
import chainlit.cli
from chainlit import on_chat_start, on_message, on_settings_update, on_stop

# Local imports
from agentic_fleet.config import config_manager
from agentic_fleet.config.llm_config_manager import llm_config_manager
from agentic_fleet.core.agents.team import initialize_default_agents
from agentic_fleet.core.application.manager import ApplicationConfig, ApplicationManager
from agentic_fleet.services.client_factory import create_client
from agentic_fleet.ui.components.mcp_panel import list_available_mcps
from agentic_fleet.ui.message_handler import handle_chat_message, on_reset
from agentic_fleet.ui.settings_handler import SettingsManager
from agentic_fleet.ui.task_manager import initialize_task_list

# Import MCP handlers to register them with Chainlit
# This import is used for its side effects (registering action callbacks)
# pylint: disable=unused-import
try:
    import agentic_fleet.pool.mcp.mcp_handlers as mcp_handlers  # noqa
except ImportError:
    pass

# Load environment variables after all imports
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AppContext:
    """Context class to encapsulate app-wide state."""

    def __init__(self) -> None:
        """Initialize the application context."""
        self.client: Any = None
        self.app_manager: Optional[ApplicationManager] = None
        self._cleanup_tasks: List[asyncio.Task] = []

    async def cleanup(self) -> None:
        """Clean up application resources."""
        if self.app_manager:
            try:
                await self.app_manager.shutdown()
                logger.info("Application manager stopped")
            except Exception as e:
                logger.warning(f"Application manager cleanup error: {str(e)}")

        # Cancel any pending tasks
        for task in self._cleanup_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


app_context = AppContext()

# Initialize settings manager
settings_manager = SettingsManager()


@on_chat_start
async def start_chat() -> None:
    """Initialize the chat session with the selected profile."""
    try:
        # Get the selected chat profile
        profile: Optional[str] = cl.user_session.get("chat_profile")
        profile_name: str = profile if isinstance(profile, str) else "default"
        logger.info(f"Selected chat profile: {profile_name}")

        # Get profile configuration
        profile_config: Dict[str, Any] = llm_config_manager.get_profile_config(profile_name)
        model_config: Dict[str, Any] = profile_config.get("model_config", {})
        model_name: str = model_config.get("name", "o4-mini")
        profile_desc: str = profile_config.get("description", "Azure OpenAI o4-mini Model")
        icon: str = profile_config.get("icon", "public/icons/rocket.svg")

        # Store profile type in session
        cl.user_session.set("profile_type", profile_name)

        # Initialize configuration
        config_manager.load_all()
        logger.info("Successfully loaded all configurations")

        # Validate environment
        if error := config_manager.validate_environment():
            raise ValueError(error)

        # Get environment settings
        env_config: Any = config_manager.get_environment_settings()

        # Use profile-specific model_config for client creation
        logger.info(f"Creating client for model {model_name} with profile config")
        try:
            # Check required environment variables
            required_env_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_VERSION"]
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                raise ValueError(f"Missing required Azure OpenAI environment variables: {', '.join(missing_vars)}")

            app_context.client = create_client(
                model_name=model_name,
                model_config=model_config,
                streaming=model_config.get("streaming", True),
                vision=model_config.get("vision", True),
                connection_pool_size=model_config.get("connection_pool_size", 10),
                request_timeout=model_config.get("request_timeout", 30),
            )
        except Exception as e:
            error_msg = f"Failed to create model client for model {model_name}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        logger.info(
            f"Created client for model {model_name} with streaming={model_config.get('streaming', True)}, vision={model_config.get('vision', True)}"
        )

        # Initialize application manager
        app_context.app_manager = ApplicationManager(
            config=ApplicationConfig(
                project_root=Path(__file__).resolve().parent.parent,
                debug=getattr(env_config, "debug", False),
                log_level=getattr(env_config, "log_level", "INFO"),
            ),
            model_client=app_context.client,
        )
        await app_context.app_manager.start()

        # Initialize task list
        await initialize_task_list()

        # Initialize agent based on profile
        agents = initialize_default_agents(model_client=app_context.client)
        team = agents[0] if agents else None
        profile_desc, icon = get_profile_metadata(profile_name)

        # Store team and profile info in user session
        cl.user_session.set("agent_team", team)
        cl.user_session.set("profile_icon", icon)

        # Set up default settings
        default_settings: Dict[str, Any] = settings_manager.get_default_settings()
        cl.user_session.set("settings", default_settings)

        # Setup chat settings UI
        await settings_manager.setup_chat_settings()

        # Send welcome message
        await send_welcome_message(profile_name, model_name, default_settings, profile_desc)

    except Exception as e:
        error_msg: str = f"⚠️ Initialization failed: {str(e)}"
        logger.error(f"Chat start error: {traceback.format_exc()}")
        await cl.Message(content=error_msg).send()


def get_profile_metadata(profile_name: str) -> Tuple[str, str]:
    """Get profile description and icon based on profile name.

    Args:
        profile_name: The name of the profile

    Returns:
        Tuple of (profile_description, icon_path)
    """
    try:
        # Get profile configuration
        profile_config: Dict[str, Any] = llm_config_manager.get_profile_config(profile_name)
        description: str = profile_config.get("description", "Standard AgenticFleet Profile")
        icon: str = profile_config.get("icon", "public/icons/rocket.svg")
        return description, icon
    except ValueError:
        # Fallback to defaults if profile not found
        if profile_name == "MCP Focus":
            return "MCP Interaction Profile", "public/icons/microscope.svg"
        return "Standard AgenticFleet Profile", "public/icons/rocket.svg"


async def send_welcome_message(profile_name: str, model_name: str, settings: Dict[str, Any], profile_desc: str) -> None:
    """Send a welcome message with profile information.

    Args:
        profile_name: The name of the profile
        model_name: The name of the model
        settings: The settings dictionary
        profile_desc: The profile description
    """
    welcome_message: str = (
        f"🚀 Welcome to AgenticFleet!\n\n"
        f"**Active Profile**: {profile_name}\n"
        f"**Model**: {model_name}\n"
        f"**Temperature**: {settings.get('temperature', 0.7)}\n\n"
        f"{profile_desc}"
    )

    # Create actions list
    actions: List[cl.Action] = [
        cl.Action(
            name="reset_agents",
            label="🔄 Reset Agents",
            tooltip="Restart the agent team",
            payload={"action": "reset"},
        )
    ]

    # Add MCP-specific action if profile is MCP Focus
    if profile_name == "MCP Focus":
        actions.append(
            cl.Action(
                name="list_mcp_tools",
                label="🛠️ List MCP Tools",
                tooltip="Show available MCP tools",
                payload={"action": "list_mcp"},
            )
        )

    # Get profile icon
    icon: str = cl.user_session.get("profile_icon") or "public/icons/rocket.svg"

    # Create elements list with avatar image
    elements = [cl.Image(name="avatar", url=icon, display="inline", size="small")]

    # Create and send message
    msg = cl.Message(content=welcome_message, author=profile_name, actions=actions, elements=elements)

    await msg.send()


@on_message
async def message_handler(message: cl.Message) -> None:
    """Handle incoming chat messages."""
    try:
        # Get the current profile type
        profile_type = cl.user_session.get("profile_type", "default")

        # Process the message
        await handle_chat_message(message)
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(f"Message handler error: {traceback.format_exc()}")
        await cl.Message(content=error_msg, author="System").send()


@on_settings_update
async def handle_settings_update(settings: Dict[str, Any]) -> None:
    """Handle updates to chat settings."""
    try:
        await settings_manager.handle_settings_update(settings)
    except Exception as e:
        logger.error(f"Settings update error: {str(e)}")
        await cl.Message(content=f"Failed to update settings: {str(e)}", author="System").send()


@cl.action_callback("reset_agents")
async def on_action_reset(action: cl.Action) -> None:
    """Handle reset action."""
    try:
        await on_reset(action)
    except Exception as e:
        logger.error(f"Reset action error: {str(e)}")
        await cl.Message(content=f"Failed to reset agents: {str(e)}", author="System").send()


@cl.action_callback("list_mcp_tools")
async def on_action_list_mcp(_: cl.Action) -> None:
    """Handle list MCP tools action."""
    try:
        # List available MCP configurations
        mcp_servers = await list_available_mcps()

        # Store the servers in the session for later use
        cl.user_session.set("mcp_servers", mcp_servers)

    except Exception as e:
        error_msg = f"Error retrieving MCP configurations: {str(e)}"
        logger.error(f"Error listing MCP configurations: {traceback.format_exc()}")
        await cl.Message(content=error_msg, author="System").send()


@on_stop
async def on_chat_stop() -> None:
    """Clean up resources when the chat is stopped."""
    try:
        # Clean up application resources
        await app_context.cleanup()

        # Reset session values
        session_keys = ["chat_profile", "profile_type", "agent_team", "profile_icon", "settings", "mcp_servers"]
        for key in session_keys:
            try:
                cl.user_session.set(key, None)
            except Exception as e:
                logger.warning(f"Failed to reset session key {key}: {str(e)}")

    except Exception as e:
        logger.error(f"Chat stop error: {str(e)}")


def main() -> None:
    """Run the Chainlit application."""
    host: str = os.environ.get("CHAINLIT_HOST", "0.0.0.0")
    port_env: str = os.environ.get("CHAINLIT_PORT", "8080")

    try:
        port: int = int(port_env)
        if not (0 < port < 65536):
            port = 8080
    except ValueError:
        port = 8080

    logger.info(f"Starting Chainlit UI on {host}:{port}")

    try:
        result = subprocess.run(
            ["chainlit", "run", os.path.abspath(__file__), "--host", host, "--port", str(port), "--no-cache"],
            check=True,
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        logger.error("Chainlit command not found. Make sure chainlit is installed.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Chainlit process failed with return code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        logger.error(f"Failed to start Chainlit: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
