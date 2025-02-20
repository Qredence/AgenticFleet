"""
OrchestratorAgent: A custom agent derived from BaseChatAgent, responsible for
coordinating multiple agents.
"""

import logging
from typing import Sequence

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core import CancellationToken

from .base_model_agent import BaseModelAgent


class OrchestratorAgent(BaseModelAgent):
    """
    An agent responsible for orchestrating the conversation flow between
    multiple agents. It receives input, delegates tasks, and manages
    the overall conversation.
    """

    def __init__(self, name: str, description: str = "Orchestrator Agent"):
        super().__init__(name=name, description=description, role="Orchestrator")
        self._message_history: list[ChatMessage] = []

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        """
        Orchestrates the action among multiple agents based on instructions
        and conversation content. This is a placeholder for more complex logic.
        """
        self._message_history.extend(messages)
        orchestrate_output = "Orchestration plan executed, delegating sub-tasks among agents. (Placeholder)"
        response_message = TextMessage(content=orchestrate_output, source=self.name)
        self._message_history.append(response_message)
        return Response(chat_message=response_message)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        logging.info(f"[OrchestratorAgent] Resetting {self.name}")
        self._message_history.clear()
