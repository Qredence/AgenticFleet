"""
This module defines the base agent class for specialized agents.

The base agent class provides common functionality for all specialized agents
in the system (Mind Map Agent, Web Search Agent, Coding Agent, etc.).
It follows patterns from Microsoft Autogen documentation.
"""

import logging
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core.models import ChatCompletionClient
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """
    Configuration model for BaseAgent.

    Attributes:
        name: The name of the agent
        description: A description of the agent's capabilities
        system_message: The system message that defines the agent's behavior
        model: The model identifier to use with this agent
    """

    name: str
    description: str | None = None
    system_message: str | None = None
    model: str | None = None


class BaseAgent(AssistantAgent):
    """
    Base agent class that extends AssistantAgent from autogen-core.

    This class provides common functionality for all specialized agents
    in the system. It handles basic agent operations like processing messages,
    generating responses, and managing agent configuration.

    Attributes:
        component_type: The type of component this agent represents
        version: The version of this agent implementation
    """

    component_type = "agent"
    version = "0.1.0"

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient | None = None,
        description: str | None = None,
        system_message: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new BaseAgent instance.

        Args:
            name: The name of this agent instance
            model_client: The model client to use for this agent
            description: A description of this agent's capabilities
            system_message: The system message that defines this agent's behavior
            **kwargs: Additional keyword arguments for agent configuration
        """
        super().__init__(
            name=name,
            system_message=system_message or self._get_default_system_message(),
            model_client=model_client,
            description=description or self._get_default_description(),
            **kwargs,
        )
        self._initialize_agent(**kwargs)

    def _get_default_system_message(self) -> str:
        """
        Get the default system message for this agent type.

        This method can be overridden by specialized agents to provide
        a custom default system message.

        Returns:
            str: The default system message
        """
        return f"You are {self.name}, a helpful AI assistant."

    def _get_default_description(self) -> str:
        """
        Get the default description for this agent type.

        This method can be overridden by specialized agents to provide
        a custom default description.

        Returns:
            str: The default description
        """
        return "An agent that provides assistance with ability to use tools."

    def _initialize_agent(self, **kwargs: Any) -> None:
        """
        Perform any additional initialization specific to this agent type.

        This method can be overridden by specialized agents to perform
        custom initialization steps.

        Args:
            **kwargs: Additional keyword arguments for agent initialization
        """
        pass

    async def process_message(self, message: str | ChatMessage) -> dict[str, Any]:
        """
        Process an incoming message and generate a response.

        This method handles both string messages and ChatMessage objects,
        converting strings to TextMessage objects if necessary.

        Args:
            message: The input message to process

        Returns:
            Dict[str, Any]: A dictionary containing the agent's response and metadata
        """
        if isinstance(message, str):
            message = TextMessage(content=message, source="user")

        response = await self.generate_response(messages=[message])
        return {"content": response.content, "role": "assistant", "metadata": response.model_dump()}

    async def run(self, task: str | list[ChatMessage]) -> dict[str, Any]:
        """
        Execute the agent's primary task.

        This method handles both string tasks and lists of ChatMessage objects,
        converting strings to TextMessage objects if necessary.

        Args:
            task: The task description or list of messages to process

        Returns:
            Dict[str, Any]: A dictionary containing the task results and metadata
        """
        if isinstance(task, str):
            task = [TextMessage(content=task, source="user")]

        response = await self.generate_response(messages=task)
        return {"content": response.content, "role": "assistant", "metadata": response.model_dump()}

    def dump_component(self) -> dict[str, Any]:
        """
        Dump the agent configuration to a dictionary format.

        This method serializes the agent's configuration for storage or transmission.

        Returns:
            Dict[str, Any]: A dictionary containing the agent's configuration
        """
        config = AgentConfig(
            name=self.name,
            description=self.description,
            system_message=self.system_message,
            model=getattr(self.model_client, "model", None),
        )

        return {
            "provider": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "component_type": self.component_type,
            "version": self.version,
            "component_version": 1,
            "description": self.description,
            "label": self.__class__.__name__,
            "config": config.model_dump(),
        }

    @classmethod
    def load_component(cls, config: dict[str, Any]) -> "BaseAgent":
        """
        Load an agent from a configuration dictionary.

        This class method creates a new agent instance from a serialized configuration.

        Args:
            config: Configuration dictionary from dump_component

        Returns:
            BaseAgent: An instance of the agent
        """
        agent_config = AgentConfig(**config["config"])
        return cls(
            name=agent_config.name,
            description=agent_config.description,
            system_message=agent_config.system_message,
        )
