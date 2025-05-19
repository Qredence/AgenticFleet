"""Default agents for the Chainlit UI."""

import os
from collections.abc import Coroutine
from dataclasses import dataclass
from typing import (
    Any,
    Protocol,
    TypedDict,
    Union,
)

from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.base import ChatAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor


# Type definitions
class ConfigManager(Protocol):
    def get_agent_settings(self, agent_name: str) -> dict[str, Any] | None: ...


class AppManager(Protocol):
    @property
    def model_client(self) -> ChatCompletionClient: ...


class AgentConfig(TypedDict, total=False):
    description: str
    config: dict[str, Any]


@dataclass
class EnvConfig:
    workspace_dir: str
    downloads_dir: str
    debug_dir: str


# Type aliases
AgentTeam = Union[MagenticOneGroupChat, SelectorGroupChat]
AgentTeamCoroutine = Coroutine[Any, Any, AgentTeam]


def initialize_default_agents(
    app_manager: AppManager,
    config_manager: ConfigManager,
    user_session: dict[str, Any],
    defaults: dict[str, Any],
    env_config: dict[str, str],
) -> dict[str, ChatAgent]:
    """
    Initialize and return a dictionary of default agents.

    Args:
        app_manager: Application manager instance providing model client
        config_manager: Configuration manager for agent settings
        user_session: User session data containing preferences
        defaults: Default configuration values
        env_config: Environment configuration with paths

    Returns:
        Dictionary mapping agent names to their instances

    Raises:
        ValueError: If required environment paths are missing
        RuntimeError: If agent initialization fails
    """
    # Validate environment configuration
    required_paths = ["workspace_dir", "downloads_dir", "debug_dir"]
    missing_paths = [path for path in required_paths if path not in env_config]
    if missing_paths:
        raise ValueError(f"Missing required environment paths: {', '.join(missing_paths)}")

    # Default descriptions for agents
    default_descriptions = {
        "web_surfer": "Web navigation and information gathering agent",
        "file_surfer": "File system navigation and management agent",
        "executor": "Code execution and command running agent",
    }

    try:
        # Initialize WebSurfer
        web_surfer_config = config_manager.get_agent_settings("web_surfer") or {}
        surfer = MultimodalWebSurfer(
            name="WebSurfer",
            model_client=app_manager.model_client,
            description=web_surfer_config.get("description", default_descriptions["web_surfer"]),
            downloads_folder=env_config["downloads_dir"],
            debug_dir=env_config["debug_dir"],
            headless=True,
            start_page=user_session.get("start_page", defaults.get("start_page")),
            animate_actions=False,
            to_save_screenshots=True,
            use_ocr=False,
            to_resize_viewport=True,
        )

        # Initialize FileSurfer
        file_surfer_config = config_manager.get_agent_settings("file_surfer") or {}
        file_surfer = FileSurfer(
            name="FileSurfer",
            model_client=app_manager.model_client,
            description=file_surfer_config.get("description", default_descriptions["file_surfer"]),
        )

        # Initialize Coder
        coder = MagenticOneCoderAgent(name="Coder", model_client=app_manager.model_client)

        # Initialize Executor
        workspace_dir = os.path.join(os.getcwd(), env_config["workspace_dir"])
        executor_settings = config_manager.get_agent_settings("executor") or {}
        code_executor = LocalCommandLineCodeExecutor(
            work_dir=workspace_dir,
            timeout=executor_settings.get("config", {}).get("timeout", 60),
        )

        executor = CodeExecutorAgent(
            name="Executor",
            code_executor=code_executor,
            description=executor_settings.get("description", default_descriptions["executor"]),
        )

        return {
            "websurfer": surfer,
            "filesurfer": file_surfer,
            "coder": coder,
            "executor": executor,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to initialize agents: {str(e)}") from e


async def initialize_agent_team(
    app_manager: AppManager,
    user_session: dict[str, Any],
    team_config: dict[str, Any],
    default_agents: dict[str, ChatAgent],
    defaults: dict[str, Any],
) -> AgentTeam:
    """
    Initialize and return an agent team based on the active profile.

    Args:
        app_manager: The application manager instance
        user_session: The user's session data
        team_config: Configuration for the team
        default_agents: Dictionary of initialized default agents
        defaults: Default configuration values

    Returns:
        An initialized agent team (MagenticOneGroupChat or SelectorGroupChat)

    Raises:
        ValueError: If required agents are missing or configuration is invalid
        RuntimeError: If team initialization fails
    """
    active_profile = user_session.get("active_chat_profile", "MagenticFleet One")
    model_client = app_manager.model_client

    # Validate default_agents
    required_agents = ["websurfer", "filesurfer", "coder", "executor"]
    missing_agents = [agent for agent in required_agents if agent not in default_agents]
    if missing_agents:
        raise ValueError(f"Missing required agents: {', '.join(missing_agents)}")

    # Create termination conditions
    config = team_config.get("config", {})
    max_messages = config.get("max_messages", 50)

    if active_profile == "MagenticFleet One":
        try:
            team = MagenticOneGroupChat(
                model_client=model_client,
                participants=[
                    default_agents["websurfer"],
                    default_agents["filesurfer"],
                    default_agents["coder"],
                    default_agents["executor"],
                ],
                max_turns=user_session.get("max_rounds", defaults.get("max_rounds", 10)),
                max_stalls=user_session.get("max_stalls", defaults.get("max_stalls", 3)),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MagenticOneGroupChat: {str(e)}") from e
    else:
        try:
            participants = []
            for agent_name in team_config.get("participants", []):
                key = agent_name.lower()
                if key in default_agents:
                    participants.append(default_agents[key])

            if not participants:
                raise ValueError("No valid participants found in team configuration")

            team = SelectorGroupChat(
                agents=participants,
                model_client=model_client,
                termination_conditions=[
                    MaxMessageTermination(max_messages=max_messages),
                    TextMentionTermination(text="DONE", ignore_case=True),
                ],
                selector_description=config.get(
                    "selector_description", "Select the next agent to handle the task."
                ),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize SelectorGroupChat: {str(e)}") from e

    return team
