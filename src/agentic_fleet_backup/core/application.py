"""Core application module for AgenticFleet."""

import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv

from agentic_fleet.backend.chainlit_components.chat_settings import ChatSettings
from agentic_fleet.config import (
    config_manager,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_MAX_STALLS,
    DEFAULT_START_PAGE,
)

class AgentInitializationError(Exception):
    """Exception raised when agent initialization fails."""
    pass

# Initialize configuration
load_dotenv()
config_manager.load_all()
logger = logging.getLogger(__name__)

# Load team configurations from fleet config
TEAM_CONFIGURATIONS = config_manager.get_team_settings("magentic_fleet_one").get("teams", {})

def create_chat_profile(
    team_config: str = "default",
    model_client: Optional[AzureOpenAIChatCompletionClient] = None,
) -> Dict[str, Any]:
    """Create a chat profile with specified configuration.

    Args:
        team_config: Team configuration key
        model_client: Azure OpenAI model client

    Returns:
        Dict containing chat profile configuration
    """
    config = TEAM_CONFIGURATIONS.get(team_config, TEAM_CONFIGURATIONS["default"])

    return {
        "name": config["name"],
        "description": config["description"],
        "max_rounds": config.get("max_rounds", DEFAULT_MAX_ROUNDS),
        "max_stalls": config.get("max_stalls", DEFAULT_MAX_STALLS),
        "model_client": model_client,
        "team_config": team_config,
    }

def create_chat_profile_with_code_execution(
    workspace_dir: str,
    team_config: str = "default",
    execution_timeout: int = 300,
) -> Dict[str, Any]:
    """Create a chat profile with code execution capabilities.

    Args:
        workspace_dir: Directory for code execution
        team_config: Team configuration key
        execution_timeout: Code execution timeout in seconds

    Returns:
        Dict containing chat profile with code execution configuration
    """
    profile = create_chat_profile(team_config)
    profile["workspace_dir"] = workspace_dir
    profile["execution_timeout"] = execution_timeout
    return profile

class ApplicationManager:
    """Manages application lifecycle and resources."""

    def __init__(self, model_client: AzureOpenAIChatCompletionClient):
        """Initialize application manager.

        Args:
            model_client: Azure OpenAI model client
        """
        self.model_client = model_client
        self._initialized = False
        self.agent_team = None
        self.teams: Dict[str, MagenticOneGroupChat] = {}
        self.settings = None

    async def start(self) -> None:
        """Start the application and initialize resources."""
        if self._initialized:
            logger.warning("Application already initialized")
            return

        try:
            logger.info("Starting application...")
            # Initialize resources here
            self._initialized = True
            logger.info("Application started successfully")

        except Exception as e:
            logger.error(f"Failed to start application: {str(e)}")
            raise

    async def stop(self) -> None:
        """Stop the application and cleanup resources."""
        if not self._initialized:
            logger.warning("Application not initialized")
            return

        try:
            logger.info("Stopping application...")
            # Cleanup resources here
            self._initialized = False
            logger.info("Application stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop application: {str(e)}")
            raise

    async def process_message(self, message: str, settings: ChatSettings) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """Process a message using the current agent team.

        Args:
            message: The message to process
            settings: Current chat settings

        Yields:
            Response chunks from the agent team
        """
        if not self._initialized:
            raise RuntimeError("Application not initialized")

        if not self.agent_team:
            # Initialize agent team if not already done
            self.agent_team = await self.initialize_agent_team()

        try:
            # Process message through agent team
            async for response in self.agent_team.process_chat(message):
                yield response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            yield {"type": "error", "message": str(e)}

    async def initialize_agent_team(self) -> MagenticOneGroupChat:
        """Initialize the agent team with current settings.

        Returns:
            Configured agent team
        """
        try:
            # Create agent team using current model client
            team = await self.create_agent_team(self.model_client)
            return team

        except Exception as e:
            logger.error(f"Failed to initialize agent team: {str(e)}")
            raise

    async def create_agent_team(self, model_client: AzureOpenAIChatCompletionClient) -> MagenticOneGroupChat:
        """Create and configure the agent team.

        Args:
            model_client: Azure OpenAI model client

        Returns:
            Configured agent team
        """
        # Get agent configurations
        agent_configs = config_manager.get_agent_settings("magentic_fleet_one")
        
        # Create agents based on configuration
        agents = []
        for agent_name, agent_config in agent_configs.get("agents", {}).items():
            if agent_config["type"] == "MultimodalWebSurfer":
                agents.append(
                    MultimodalWebSurfer(
                        name=agent_name,
                        model_client=model_client,
                        description=agent_config["description"],
                        **agent_config.get("config", {})
                    )
                )
            elif agent_config["type"] == "FileSurfer":
                agents.append(
                    FileSurfer(
                        name=agent_name,
                        model_client=model_client,
                        description=agent_config["description"]
                    )
                )
            elif agent_config["type"] == "MagenticOneCoderAgent":
                agents.append(
                    MagenticOneCoderAgent(
                        name=agent_name,
                        model_client=model_client,
                        description=agent_config["description"],
                        **agent_config.get("config", {})
                    )
                )
            elif agent_config["type"] == "CodeExecutorAgent":
                executor = LocalCommandLineCodeExecutor(**agent_config.get("executor_config", {}))
                agents.append(
                    CodeExecutorAgent(
                        name=agent_name,
                        code_executor=executor,
                        description=agent_config["description"]
                    )
                )

        # Create team with configured agents
        team = MagenticOneGroupChat(
            participants=agents,
            model_client=model_client,
            max_turns=DEFAULT_MAX_ROUNDS,
            max_stalls=DEFAULT_MAX_STALLS,
        )

        return team

    async def create_team(
        self,
        profile: Dict[str, Any],
        model_client: Optional[AzureOpenAIChatCompletionClient] = None,
    ) -> MagenticOneGroupChat:
        """Create a new agent team based on profile configuration.

        Args:
            profile: Chat profile configuration
            model_client: Azure OpenAI model client

        Returns:
            Configured agent team
        """
        try:
            team_config = config_manager.get_team_settings(profile.get("team_config", "default"))
            agents = []

            for agent_name in team_config.get("participants", []):
                agent_config = config_manager.get_agent_settings(agent_name)
                if not agent_config:
                    continue

                if agent_config["type"] == "MultimodalWebSurfer":
                    agents.append(
                        MultimodalWebSurfer(
                            name=agent_name,
                            model_client=model_client or self.model_client,
                            description=agent_config["description"],
                            start_page=DEFAULT_START_PAGE,
                            **agent_config.get("config", {})
                        )
                    )
                elif agent_config["type"] == "FileSurfer":
                    agents.append(
                        FileSurfer(
                            name=agent_name,
                            model_client=model_client or self.model_client,
                            description=agent_config["description"]
                        )
                    )
                elif agent_config["type"] == "MagenticOneCoderAgent":
                    agents.append(
                        MagenticOneCoderAgent(
                            name=agent_name,
                            model_client=model_client or self.model_client,
                            description=agent_config["description"],
                            **agent_config.get("config", {})
                        )
                    )
                elif agent_config["type"] == "CodeExecutorAgent":
                    executor = LocalCommandLineCodeExecutor(
                        work_dir=profile.get("workspace_dir", "./workspace"),
                        timeout=profile.get("execution_timeout", 300)
                    )
                    agents.append(
                        CodeExecutorAgent(
                            name=agent_name,
                            code_executor=executor,
                            description=agent_config["description"]
                        )
                    )

            team = MagenticOneGroupChat(
                participants=agents,
                model_client=model_client or self.model_client,
                max_turns=profile.get("max_rounds", DEFAULT_MAX_ROUNDS),
                max_stalls=profile.get("max_stalls", DEFAULT_MAX_STALLS),
            )

            team_id = f"{profile['team_config']}_{len(self.teams)}"
            self.teams[team_id] = team
            return team

        except Exception as e:
            logger.error(f"Failed to create team: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Clean up application resources."""
        for team in self.teams.values():
            try:
                await team.cleanup()
            except Exception as e:
                logger.error(f"Error during team cleanup: {str(e)}")

    def add_cleanup_handler(self, handler: callable) -> None:
        """Add a cleanup handler to be called during application shutdown.

        Args:
            handler: Cleanup handler function
        """
        # Store cleanup handler for later use
        self._cleanup_handlers = getattr(self, '_cleanup_handlers', [])
        self._cleanup_handlers.append(handler)

async def create_application(model_client: AzureOpenAIChatCompletionClient) -> ApplicationManager:
    """Create and initialize application manager.

    Args:
        model_client: Azure OpenAI model client

    Returns:
        Initialized application manager
    """
    app = ApplicationManager(model_client)
    await app.start()
    return app

async def stream_text(text: str) -> List[str]:
    """Stream text content word by word.

    Args:
        text: Text to stream

    Returns:
        List of words from the text
    """
    return text.split()
