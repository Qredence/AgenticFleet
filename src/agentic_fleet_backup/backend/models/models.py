"""Enhanced agent implementations for AgenticFleet.

This module provides enhanced versions of Autogen's agents with additional
capabilities and improved error handling.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from autogen_agentchat.agents import Agent, AssistantAgent, UserProxyAgent
from autogen_core import ChatCompletionClient


class EnhancedAssistantAgent(AssistantAgent):
    """Enhanced version of Autogen's AssistantAgent with improved capabilities."""

    def __init__(
        self,
        name: str,
        system_message: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize EnhancedAssistantAgent.

        Args:
            name: Agent name
            system_message: System message for the agent
            llm_config: LLM configuration
            **kwargs: Additional configuration options
        """
        super().__init__(
            name=name,
            system_message=system_message or "You are a helpful AI assistant.",
            llm_config=llm_config,
            **kwargs,
        )

    async def process_message(self, message: str, sender: Agent) -> str:
        """Process incoming messages with improved error handling.

        Args:
            message: Input message
            sender: Agent that sent the message

        Returns:
            Response message

        Raises:
            Exception: For message processing errors
        """
        try:
            return await super().process_message(message, sender)
        except Exception as e:
            # Log error and return graceful fallback response
            print(f"Error processing message: {e}")
            return "I apologize, but I encountered an error processing your message. Could you please rephrase or try again?"


class EnhancedUserProxyAgent(UserProxyAgent):
    """Enhanced version of Autogen's UserProxyAgent with improved capabilities."""

    def __init__(self, name: str, system_message: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize EnhancedUserProxyAgent.

        Args:
            name: Agent name
            system_message: System message for the agent
            **kwargs: Additional configuration options
        """
        super().__init__(name=name, system_message=system_message or "A human user.", **kwargs)


def create_azure_client(
    deployment: str,
    model: str,
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> ChatCompletionClient:
    """Create an Azure OpenAI chat completion client.

    Args:
        deployment: Model deployment name
        model: Model identifier
        endpoint: API endpoint
        api_key: API key
        **kwargs: Additional client configuration

    Returns:
        Configured chat completion client
    """
    from .factory import ModelFactory, ModelProvider

    client = ModelFactory.create(
        ModelProvider.AZURE_OPENAI,
        deployment=deployment,
        model=model,
        endpoint=endpoint,
        api_key=api_key,
        **kwargs,
    )
    return client


def create_agent_team(
    task: str,
    assistant_name: str = "Assistant",
    user_name: str = "User",
    llm_config: Optional[Dict[str, Any]] = None,
) -> Tuple[EnhancedAssistantAgent, EnhancedUserProxyAgent]:
    """Create a team of enhanced agents for a specific task.

    Args:
        task: Task description
        assistant_name: Name for the assistant agent
        user_name: Name for the user agent
        llm_config: LLM configuration for the assistant

    Returns:
        Tuple of (assistant agent, user agent)
    """
    assistant = EnhancedAssistantAgent(
        name=assistant_name,
        system_message=f"You are a helpful AI assistant focused on: {task}",
        llm_config=llm_config,
    )

    user = EnhancedUserProxyAgent(name=user_name, system_message=f"A human user working on: {task}")

    return assistant, user
