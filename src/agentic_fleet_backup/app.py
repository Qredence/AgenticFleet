"""Chainlit-based web interface for AutoGen agent interactions."""

# Standard library imports
import asyncio
import json
import logging
import os
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

# Third-party imports
import chainlit as cl
import yaml

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent, UserProxyAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import (
    AgentEvent,
    ChatMessage,
    FunctionCall,
    Image,
    MultiModalMessage,
    TextMessage,
)
from autogen_agentchat.teams import (
    MagenticOneGroupChat,
    SelectorGroupChat,
)
from autogen_agentchat.ui import Console
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from chainlit import (
    Message,
    Step,
    Task,
    TaskStatus,
    User,
    oauth_callback,
    on_message,
    on_settings_update,
    on_stop,
    user_session,
)
from chainlit.action import Action
from chainlit.chat_settings import ChatSettings
from chainlit.input_widget import Select, Slider, Switch
from dotenv import load_dotenv
from pydantic import BaseModel

from agentic_fleet.agent_registry import (
    initialize_agent_team,
    initialize_default_agents,
)
from agentic_fleet.backend.application_manager import ApplicationManager, Settings
from agentic_fleet.config import config_manager
from agentic_fleet.config_utils import (
    check_oauth_configuration,
    cleanup_workspace,
)
from agentic_fleet.message_processing import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_RUNNING,
    process_response,
    stream_text,
)

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize configuration manager
try:
    config_manager.load_all()
    logger.info("Successfully loaded all configurations")

    # Validate environment
    if error := config_manager.validate_environment():
        raise ValueError(error)
except Exception as e:
    logger.error(f"Configuration error: {e}")
    raise

# Get environment settings
env_config = config_manager.get_environment_settings()

# Constants
STREAM_DELAY = env_config.get("stream_delay", 0.03)
PORT = int(os.getenv("CHAINLIT_PORT", os.getenv("PORT", "8000")))
HOST = os.getenv("CHAINLIT_HOST", os.getenv("HOST", "localhost"))

# Get default values
defaults = config_manager.get_defaults()
DEFAULT_MAX_ROUNDS = defaults.get("max_rounds", 10)
DEFAULT_MAX_TIME = defaults.get("max_time", 300)
DEFAULT_MAX_STALLS = defaults.get("max_stalls", 3)
DEFAULT_START_PAGE = defaults.get("start_page", "https://www.bing.com")
DEFAULT_TEMPERATURE = defaults.get("temperature", 0.7)
DEFAULT_SYSTEM_PROMPT = defaults.get("system_prompt", "You are a helpful AI assistant.")

app_manager: Optional[ApplicationManager] = None

# OAuth configuration - only define callback if OAuth is enabled
security_config = config_manager.get_security_settings()
if security_config.get("use_oauth", False):

    @oauth_callback
    async def handle_oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: Dict[str, str],
        default_user: User,
    ) -> User:
        """Handle OAuth authentication callback."""
        return default_user


@cl.on_settings_update
async def update_settings(new_settings: dict):
    try:
        # Get profile metadata if this is a profile change
        profile_metadata = new_settings.get("profile_metadata", {})
        if profile_metadata:
            # Apply profile settings
            temperature = float(profile_metadata.get("temperature", 0.7))
            max_rounds = int(profile_metadata.get("max_rounds", 10))
            max_time = int(profile_metadata.get("max_time", 300))
            system_prompt = profile_metadata.get(
                "system_prompt", defaults.get("system_prompt")
            )
        else:
            # Apply manual settings
            temperature = float(new_settings.get("temperature", 0.7))
            max_rounds = int(new_settings.get("max_rounds", 10))
            max_time = int(new_settings.get("max_time", 300))
            system_prompt = new_settings.get(
                "system_prompt", defaults.get("system_prompt")
            )

        # Update settings in app_manager if it is initialized
        if app_manager is not None:
            app_manager.settings.temperature = temperature
            app_manager.settings.max_rounds = max_rounds
            app_manager.settings.max_time = max_time
            app_manager.settings.system_prompt = system_prompt
        else:
            logger.warning("app_manager not initialized, settings updated in session but not applied to app_manager")

        # Update the settings object in user_session if exists
        current_settings = user_session.get("settings")
        if current_settings:
            current_settings.temperature = temperature
            current_settings.max_rounds = max_rounds
            current_settings.max_time = max_time
            current_settings.system_prompt = system_prompt
            user_session.set("settings", current_settings)
        else:
            logger.warning("No settings object in session to update")

        # Update session parameters
        user_session.set("max_rounds", max_rounds)
        user_session.set("max_time", max_time)

        # Send confirmation with applied settings
        settings_text = (
            f"Settings updated:\n"
            f"• Temperature: {temperature}\n"
            f"• Max Rounds: {max_rounds}\n"
            f"• Response Time: {max_time} seconds\n"
            f"• System Prompt: {system_prompt}"
        )
        await cl.Message(content=settings_text).send()

    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        await cl.Message(content=f"⚠️ Failed to update settings: {str(e)}").send()


@cl.set_chat_profiles
async def chat_profiles():
    """Define available chat profiles."""
    return [
        cl.ChatProfile(
            name="GPT-4o-Mini",
            markdown_description="Azure OpenAI GPT-4o Mini (128k context)",
            icon="public/icons/standard.png",
            model="gpt-4o-mini",
            temperature=0.7,
            context_length=128000,
            max_tokens=4000,
            stop_sequences=None
        ),
        cl.ChatProfile(
            name="O3-Mini",
            markdown_description="Azure OpenAI O3 Mini (Specialized coding)",
            icon="public/icons/standard.png",
            model="o3-mini",
            temperature=0.7,
            context_length=128000,
            max_tokens=4000,
            stop_sequences=None
        )
    ]


async def setup_chat_settings():
    """
    Display the current chat settings retrieved from the user session.
    If settings don't exist, initialize them with defaults.
    """
    settings = user_session.get("settings")
    if not settings:
        # Initialize settings with defaults if they don't exist
        model_configs = config_manager.get_model_settings("azure_openai")
        fleet_config = config_manager.get_team_settings("magentic_fleet_one")
        azure_config = model_configs["providers"]["azure"]
        # Add default chat settings to fleet_config
        fleet_config.update({
            "temperature": DEFAULT_TEMPERATURE,
            "max_rounds": DEFAULT_MAX_ROUNDS,
            "max_time": DEFAULT_MAX_TIME,
            "system_prompt": DEFAULT_SYSTEM_PROMPT
        })
        settings = Settings(model_configs=model_configs, fleet_config=fleet_config)
        user_session.set("settings", settings)

    # Safely get settings with defaults
    temperature = getattr(settings, "temperature", DEFAULT_TEMPERATURE)
    max_rounds = getattr(settings, "max_rounds", DEFAULT_MAX_ROUNDS)
    max_time = getattr(settings, "max_time", DEFAULT_MAX_TIME)
    system_prompt = getattr(settings, "system_prompt", DEFAULT_SYSTEM_PROMPT)

    settings_desc = (
        f"Current Chat Settings:\n"
        f"• Temperature: {temperature}\n"
        f"• Max Rounds: {max_rounds}\n"
        f"• Max Time: {max_time} seconds\n"
        f"• System Prompt: {system_prompt}"
    )
    await cl.Message(content=settings_desc).send()


async def setup_chat():
    await setup_chat_settings()


@cl.on_chat_start
async def init_chat():
    """Initialize chat session with selected model."""
    try:
        # Get selected chat profile
        chat_profile = cl.user_session.get("chat_profile")
        if not chat_profile:
            model_name = "gpt-4o-mini"
        else:
            model_name = chat_profile.model if isinstance(chat_profile, cl.ChatProfile) else chat_profile
        model_name = model_name.lower()

        # Load model config
        azure_config = config_manager.get_model_settings("azure_openai")

        # Validate selected model
        if model_name not in azure_config["models"]:
            raise ValueError(f"Model {model_name} not found in configuration")

        # Initialize Azure client
        model_settings = azure_config["models"][model_name]
        client = AzureOpenAIChatCompletionClient(
            model=model_settings.get("name", model_name),
            deployment=model_settings.get("deployment", model_name),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            endpoint=model_settings.get("endpoint", os.getenv("AZURE_OPENAI_ENDPOINT")),
            api_key=model_settings.get("api_key", os.getenv("AZURE_OPENAI_API_KEY")),
            streaming=True,
            model_info={
                "vision": model_settings.get("vision", True),
                "function_calling": model_settings.get("function_calling", True),
                "json_output": model_settings.get("json_output", True),
                "family": model_settings.get("family", "azure"),
                "architecture": model_settings.get("architecture", "gpt-4o-mini")
            }
        )

        # Get environment and default settings
        env_config = config_manager.get_environment_settings()
        defaults = config_manager.get_defaults()

        # Initialize agent team
        team_config = config_manager.get_team_settings("magentic_fleet_one")
        default_agents = initialize_default_agents(
            app_manager=ApplicationManager(client),
            config_manager=config_manager,
            user_session=cl.user_session,
            defaults=defaults,
            env_config=env_config
        )
        team = initialize_agent_team(
            app_manager=ApplicationManager(client),
            user_session=cl.user_session,
            team_config=team_config,
            default_agents=default_agents,
            defaults=defaults
        )
        cl.user_session.set("team", team)

        # Send initialization message
        init_msg = cl.Message(content="")
        await init_msg.send()
        async for chunk in stream_text(
            f"✅ Connected to {model_name} through Azure OpenAI",
            STREAM_DELAY
        ):
            await init_msg.stream_token(chunk)
        await init_msg.update()

        # Initialize task list
        task_list = cl.TaskList(tasks=[])
        task_list.status = "Ready"
        cl.user_session.set("task_list", task_list)
        await task_list.send()

    except Exception as e:
        logger.error(f"Failed to initialize chat: {e}")
        await cl.Message(content=f"⚠️ Error: {str(e)}").send()


@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming messages with streaming responses."""
    try:
        team = cl.user_session.get("team")
        if not team:
            await cl.Message(content="⚠️ Session not initialized").send()
            return

        # Create root message for streaming
        root_msg = cl.Message(content="")
        await root_msg.send()

        # Process conversation stream by passing the user's message as the task
        async for response in team.run_stream(task=message.content):
            if hasattr(response, 'content') and response.content:
                # Stream token-by-token
                async for token in stream_text(response.content, STREAM_DELAY):
                    await root_msg.stream_token(token)
            # Handle other response types
            await process_response(response, collected_responses=[])

        await root_msg.update()

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        error_msg = cl.Message(content="")
        async for chunk in stream_text(
            f"⚠️ Error: {str(e)}",
            STREAM_DELAY
        ):
            await error_msg.stream_token(chunk)
        await error_msg.send()


@cl.on_stop
async def cleanup():
    """Clean up resources when chat ends."""
    try:
        team = cl.user_session.get("team")
        if team:
            await team.cleanup()
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


@cl.action_callback("open_chat_settings")
async def on_action():
    """Handle the open chat settings action by opening the chat settings dialog."""
    try:
        # Create a task list for settings operations
        task_list = cl.TaskList()
        settings_task = await task_list.add_task("Opening Settings")
        await task_list.send()

        async with cl.Step(name="Settings Dialog", type="run", show_input=True) as step:
            # Stream the opening message
            msg = cl.Message(content="")
            await msg.send()
            async for chunk in stream_text("Opening settings dialog...", STREAM_DELAY):
                await msg.stream_token(chunk)

                # Get current settings from session
                current_settings = user_session.get("settings")
                if not current_settings:
                    step.is_error = True
                    step.output = "No settings found in session"
                    settings_task.status = TASK_STATUS_FAILED
                    await task_list.send()

                    # Stream the error message
                    error_msg = cl.Message(content="")
                    await error_msg.send()
                    async for chunk in stream_text(
                        "⚠️ Failed to load settings. Please refresh the page.",
                        STREAM_DELAY,
                    ):
                        await error_msg.stream_token(chunk)
                    return {"success": False}

                # Update task status
                settings_task.status = TASK_STATUS_RUNNING
                await task_list.send()

                # Display settings dialog
                await setup_chat_settings()

                # Complete the task
                settings_task.status = TASK_STATUS_COMPLETED
                await task_list.send()

                # Stream success message
                success_msg = cl.Message(content="")
                await success_msg.send()
                async for chunk in stream_text(
                    "✅ Settings dialog opened successfully", STREAM_DELAY
                ):
                    await success_msg.stream_token(chunk)
                step.output = "Settings dialog opened successfully"
                return {"success": True}

    except Exception as e:
        logger.error(f"Failed to open settings: {str(e)}")
        if "settings_task" in locals():
            settings_task.status = TASK_STATUS_FAILED
            await task_list.send()

        error_msg = cl.Message(content="")
        async for chunk in stream_text(
            f"⚠️ Error opening settings: {str(e)}", STREAM_DELAY
        ):
            await error_msg.stream_token(chunk)
        await error_msg.send()
        return {"success": False}

