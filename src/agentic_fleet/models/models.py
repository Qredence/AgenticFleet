"""Models module for AgenticFleet.

This module provides enhanced agent models and team creation functionality.
"""

from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient


class EnhancedAssistantAgent(AssistantAgent):
    """Enhanced version of AssistantAgent with additional capabilities."""

    def __init__(
        self,
        name: str,
        system_message: str,
        model_client: ChatCompletionClient | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the enhanced assistant agent.

        Args:
            name: Name of the agent
            system_message: System message for the agent
            model_client: Optional model client for chat completion
            **kwargs: Additional arguments passed to AssistantAgent
        """
        super().__init__(
            name=name, system_message=system_message, model_client=model_client, **kwargs
        )
        self._model_client = model_client

    async def process_message(self, message: str, token: CancellationToken = None) -> Response:
        """
        Process an incoming message.

        Args:
            message: The message to process
            token: Optional cancellation token

        Returns:
            Response containing the processed result
        """
        try:
            if self._model_client:
                response = await self._model_client.generate(message)
                return Response(chat_message=TextMessage(content=str(response), source=self.name))
            return Response(
                chat_message=TextMessage(content="No model client available", source=self.name)
            )
        except Exception as e:
            return Response(
                chat_message=TextMessage(
                    content=f"Error processing message: {str(e)}", source=self.name
                )
            )


async def create_agent_team(
    agents: list[EnhancedAssistantAgent], team_config: dict[str, Any] | None = None
) -> list[EnhancedAssistantAgent]:
    """
    Create a team of agents with specified configuration.

    Args:
        agents: List of agents to include in the team
        team_config: Optional configuration for the team

    Returns:
        List of configured agents
    """
    if team_config is None:
        team_config = {}

    # Apply team configuration to each agent
    for agent in agents:
        agent_config = team_config.get(agent.name, {})
        for key, value in agent_config.items():
            setattr(agent, key, value)

    return agents
