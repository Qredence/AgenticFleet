"""
AssistantAgent: A base class for specialized assistant agents within the agentic_fleet.
It provides common functionalities and structure for agents that assist in specific tasks,
potentially managing their own 'Workies'.
"""

import logging
from typing import Any, List, Optional, Sequence

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core import CancellationToken


class AssistantAgent(BaseChatAgent):
    """
    Base class for assistant agents. Provides common functionality like
    managing workies (if applicable) and basic message handling.
    """

    def __init__(self, name: str, description: str = "Assistant Agent", workies: Optional[List[Any]] = None):
        super().__init__(name, description=description)
        self._message_history: list[ChatMessage] = []
        self.workies = workies or []  # List of WorkieAgent instances

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        """
        Handles incoming messages.  This is a basic implementation that should
        be overridden by subclasses.
        """
        self._message_history.extend(messages)
        # Default behavior: Acknowledge receipt of messages.
        response_content = f"{self.name} received: {messages[-1].content if messages else 'No new messages.'}"
        response_message = TextMessage(content=response_content, source=self.name)
        self._message_history.append(response_message)
        return Response(chat_message=response_message)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        logging.info(f"[AssistantAgent] Resetting {self.name}")
        self._message_history.clear()
        # Reset workies if any
        for workie in self.workies:
            await workie.on_reset(cancellation_token)
