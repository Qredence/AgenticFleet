"""
PlannerAgentV2: A custom planner agent derived from BaseChatAgent, demonstrating how
to create custom agents following the AutoGen architecture. It plans tasks and requests
others to perform or gather information as needed.
"""

import logging
from typing import Sequence
from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core import CancellationToken

class PlannerAgentV2(BaseChatAgent):
    """
    A specialized agent for planning. It determines how to break down a user's
    request into actionable steps or sub-tasks, delegating as required.
    Inherits from BaseChatAgent for custom behavior.
    """

    def __init__(self, name: str, description: str = "Planner Agent"):
        super().__init__(name, description=description)
        self._message_history: list[ChatMessage] = []

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        # This agent primarily produces text messages
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        """
        Called by the framework whenever the agent is tasked to respond
        synchronously (non-streaming).
        """
        # We'll store messages for contextual planning.
        self._message_history.extend(messages)
        # Minimal stub for planning
        plan_output = "Here is a plan to achieve the user's request."
        response_message = TextMessage(content=plan_output, source=self.name)
        self._message_history.append(response_message)
        return Response(chat_message=response_message)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """
        Reset the agent and clear the message history.
        """
        logging.info(f"[PlannerAgentV2] Resetting {self.name}")
        self._message_history.clear()
