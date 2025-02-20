"""AutoGen-based agent implementations.

This module implements AutoGen-compatible agents for AI-powered interactions.
It follows AutoGen's patterns for message handling, configuration, and agent lifecycle management.
Supports enhanced error handling, logging, and model configuration management.
"""

# Standard library imports
import asyncio
import logging
from typing import Any, Dict, Optional, Union

# Third-party imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_core.models import (
    AssistantMessage,  # Used in type hints
    ChatCompletionClient,
    SystemMessage,  # Used in type hints
    UserMessage,  # Used in type hints
)

from agentic_fleet.backend.models.config.factory import ModelFactory, ModelProvider

# Local imports
from agentic_fleet.backend.models.config.model_config import default_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder type hints for unused imported types
def _type_hint_placeholder() -> None:
    """Placeholder to use imported types and avoid linter warnings."""
    _: AssistantMessage = None  # type: ignore
    _: SystemMessage = None  # type: ignore
    _: UserMessage = None  # type: ignore


def create_model_client(
    provider: ModelProvider = ModelProvider.AZURE_OPENAI,
    model_key: str = "gpt4o",
    **kwargs: Any,
) -> ChatCompletionClient:
    """Create a model client with configuration from model pool.

    Args:
        provider: Model provider to use
        model_key: Key of the model in the provider's config
        **kwargs: Additional provider-specific configuration

    Returns:
        Configured model client
    """
    provider_config = default_config.get_provider_config(provider.value)
    model_config = default_config.get_model_config(provider.value, model_key)

    return ModelFactory.create(
        provider,
        model=model_config["name"],
        model_info=model_config["capabilities"],
        **{**provider_config, **kwargs},
    )


class AssistantAgent(AssistantAgent):
    """AutoGen assistant agent with improved capabilities.

    Features:
    - Configurable model selection from model pool
    - Enhanced error handling and logging
    - Automatic model capability detection
    - Support for streaming responses
    """

    def __init__(
        self,
        name: str,
        system_message: str,
        provider: ModelProvider = ModelProvider.AZURE_OPENAI,
        model_key: str = "gpt4o",
        model_client: Optional[ChatCompletionClient] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the assistant agent.

        Args:
            name: Agent name
            system_message: System message defining agent behavior
            provider: Model provider to use if no client provided
            model_key: Key of the model in provider's config
            model_client: Optional pre-configured model client
            **kwargs: Additional agent configuration
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(
            "Initializing assistant agent",
            extra={
                "agent_name": name,
                "provider": provider.value,
                "model_key": model_key,
            },
        )

        # Create or use provided model client
        model_client = model_client or create_model_client(provider, model_key)

        super().__init__(
            name=name,
            system_message=system_message,
            model_client=model_client,
            **kwargs,
        )

    async def process_message(
        self, message: Union[str, Dict], context: Optional[Any] = None
    ) -> Union[str, Dict]:
        """Process incoming messages with enhanced error handling.

        Args:
            message: Input message (string or dict format)
            context: Optional message context

        Returns:
            Processed response

        Raises:
            Exception: If message processing fails
        """
        try:
            self.logger.debug(
                "Processing message",
                extra={"agent_name": self.name, "message_type": type(message).__name__},
            )
            return await super().process_message(message, context)
        except Exception as e:
            self.logger.error(
                "Error processing message",
                extra={"agent_name": self.name, "error": str(e)},
                exc_info=True,
            )
            raise


class UserProxyAgent(UserProxyAgent):
    """AutoGen user proxy agent with improved capabilities.

    Features:
    - Enhanced error handling and logging
    - Support for structured message formats
    - Improved context handling
    """

    def __init__(self, name: str, system_message: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize the user proxy agent.

        Args:
            name: Agent name
            system_message: Optional system message
            **kwargs: Additional agent configuration
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initializing user proxy agent", extra={"agent_name": name})

        super().__init__(
            name=name,
            system_message=system_message or "You are a helpful user proxy.",
            **kwargs,
        )

    async def process_message(
        self, message: Union[str, Dict], context: Optional[Any] = None
    ) -> Union[str, Dict]:
        """Process incoming messages with enhanced error handling.

        Args:
            message: Input message (string or dict format)
            context: Optional message context

        Returns:
            Processed response

        Raises:
            Exception: If message processing fails
        """
        try:
            self.logger.debug(
                "Processing message",
                extra={"agent_name": self.name, "message_type": type(message).__name__},
            )
            return await super().process_message(message, context)
        except Exception as e:
            self.logger.error(
                "Error processing message",
                extra={"agent_name": self.name, "error": str(e)},
                exc_info=True,
            )
            raise


def create_agent_team(
    task: str,
    provider: ModelProvider = ModelProvider.AZURE_OPENAI,
    model_key: str = "gpt4o",
    model_client: Optional[ChatCompletionClient] = None,
) -> MagenticOneGroupChat:
    """Create a team of agents for collaborative task solving.

    Args:
        task: The task to be solved
        provider: Model provider to use if no client provided
        model_key: Key of the model in provider's config
        model_client: Optional pre-configured model client

    Returns:
        A configured group chat team
    """
    logger.info(
        "Creating agent team",
        extra={"task": task, "provider": provider.value, "model_key": model_key},
    )

    # Create or use provided model client
    model_client = model_client or create_model_client(provider, model_key)

    # Create the team coordinator
    coordinator = AssistantAgent(
        name="coordinator",
        system_message="""You are the team coordinator.
        Break down tasks and delegate to appropriate team members.
        Ensure all contributions align with the overall goal.
        Provide clear instructions and feedback.""",
        model_client=model_client,
    )

    # Create specialized agents
    researcher = AssistantAgent(
        name="researcher",
        system_message="""You are the research specialist.
        Gather and analyze information relevant to the task.
        Provide well-researched insights and recommendations.""",
        model_client=model_client,
    )

    implementer = AssistantAgent(
        name="implementer",
        system_message="""You are the implementation specialist.
        Convert plans and research into concrete solutions.
        Focus on practical, efficient implementations.""",
        model_client=model_client,
    )

    reviewer = AssistantAgent(
        name="reviewer",
        system_message="""You are the quality reviewer.
        Evaluate solutions for correctness and completeness.
        Suggest improvements and catch potential issues.""",
        model_client=model_client,
    )

    # Create user proxy
    user_proxy = UserProxyAgent(name="user", system_message=f"Task to solve: {task}")

    # Create and configure the group chat
    return MagenticOneGroupChat(
        agents=[coordinator, researcher, implementer, reviewer, user_proxy],
        messages=[],
        max_round=10,
    )


async def main():
    """Example usage of the AutoGen-based agent system."""
    task = "Design and implement a REST API for a todo list application"
    team = create_agent_team(task)

    try:
        await team.run()
    except Exception as e:
        logger.error("Error running agent team", exc_info=True)
        raise e


if __name__ == "__main__":
    asyncio.run(main())
