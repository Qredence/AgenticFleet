"""
CapabilityAssessorAgent: A custom agent derived from BaseChatAgent, responsible for
assessing whether the available agents and tools can fulfill the requirements of a given plan.
"""

import logging
from typing import Any, Dict, Optional, Sequence

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core import CancellationToken


class CapabilityAssessorAgent(BaseChatAgent):
    """
    An agent that assesses the capabilities of available agents and tools against
    a given plan. It determines if the current setup can handle the tasks outlined
    in the plan.
    """

    def __init__(self, name: str, description: str = "Capability Assessor Agent", agent_registry: Optional[Dict[str, Any]] = None):
        super().__init__(name, description=description)
        self._message_history: list[ChatMessage] = []
        # agent_registry:  A simple dictionary for this example.  In a real
        # application, this could be a more sophisticated system.  Keys are
        # agent/tool names, values are dictionaries of capabilities.
        self.agent_registry = agent_registry or {}

    @property
    def produced_message_types(self) -> Sequence[type[ChatMessage]]:
        return (TextMessage,)

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        """
        Analyzes a plan (provided in the messages) and assesses if the current
        agent and tool registry has the capabilities to execute the plan.
        """
        self._message_history.extend(messages)

        # Assume the last message contains the plan.  A more robust implementation
        # might use a structured message type or a dedicated planning message.
        if not messages:
            return Response(chat_message=TextMessage(content="No plan provided.", source=self.name))

        last_message = messages[-1]
        if not isinstance(last_message, TextMessage) or not last_message.content:
             return Response(chat_message=TextMessage(content="No plan provided.", source=self.name))

        plan_text = last_message.content

        # Very basic capability assessment.  This is a placeholder for more
        # sophisticated logic.
        if "research" in plan_text.lower() and "ResearchAgent" not in self.agent_registry:
            response_content = "Capability assessment failed: Missing ResearchAgent."
        elif "code execution" in plan_text.lower() and "FleetWorker" not in self.agent_registry:
            response_content = "Capability assessment failed: Missing FleetWorker for code execution."
        elif "tool use" in plan_text.lower() and "ToolCallerAgent" not in self.agent_registry:
            response_content = "Capability assessment failed: Missing ToolCallerAgent."
        else:
            response_content = "Capability assessment successful: The current agent pool can handle the plan."

        response_message = TextMessage(content=response_content, source=self.name)
        self._message_history.append(response_message)
        return Response(chat_message=response_message)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        logging.info(f"[CapabilityAssessorAgent] Resetting {self.name}")
        self._message_history.clear()
