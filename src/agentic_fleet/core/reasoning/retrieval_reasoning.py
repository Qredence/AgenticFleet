"""
Retrieval Reasoning Orchestrator Module.

This module implements the retrieval-reasoning pattern using Autogen 0.4.7's
architecture for dynamic multi-agent interactions.
"""

from collections.abc import Sequence

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ChatMessage, TextMessage
from autogen_core import CancellationToken
from autogen_core.models._model_client import CreateResult, LLMMessage, RequestUsage


class RetrievalReasoningOrchestrator(BaseChatAgent):
    """
    Orchestrates the iterative retrieval-and-reasoning process using Autogen's
    multi-agent patterns.
    """

    def __init__(
        self,
        name: str = "retrieval_reasoning_orchestrator",
        mind_map_agent: BaseChatAgent = None,
        web_search_agent: BaseChatAgent = None,
        coding_agent: BaseChatAgent = None,
        max_iterations: int = 5,
        **kwargs,
    ):
        """
        Initialize the orchestrator with specialized agents.

        Args:
            name: Name of the orchestrator agent
            mind_map_agent: Agent for knowledge graph operations
            web_search_agent: Agent for web search operations
            coding_agent: Agent for code generation/execution
            max_iterations: Maximum number of reasoning iterations
            **kwargs: Additional arguments passed to BaseChatAgent
        """
        super().__init__(name=name, **kwargs)
        self.mind_map_agent = mind_map_agent
        self.web_search_agent = web_search_agent
        self.coding_agent = coding_agent
        self.max_iterations = max_iterations

    async def _handle_web_search(self, query: str, token: CancellationToken = None) -> Response:
        """Handle web search token by delegating to web search agent."""
        if not self.web_search_agent:
            return Response(content="Web search agent not configured")

        message = TextMessage(content=query, role="user")
        response = await self.web_search_agent.process_message(message, token)
        return response

    async def _handle_coding(self, task: str, token: CancellationToken = None) -> Response:
        """Handle coding token by delegating to coding agent."""
        if not self.coding_agent:
            return Response(content="Coding agent not configured")

        message = TextMessage(content=task, role="user")
        response = await self.coding_agent.process_message(message, token)
        return response

    async def _handle_mind_map(self, query: str, token: CancellationToken = None) -> Response:
        """Handle mind map token by delegating to mind map agent."""
        if not self.mind_map_agent:
            return Response(content="Mind map agent not configured")

        message = TextMessage(content=query, role="user")
        response = await self.mind_map_agent.process_message(message, token)
        return response

    async def _process_token_in_text(self, text: str, token_type: str) -> Response | None:
        """Extract and process a specific token type from text."""
        start_token = f"[{token_type}:"
        end_token = "]"

        if start_token in text:
            start_idx = text.find(start_token) + len(start_token)
            end_idx = text.find(end_token, start_idx)
            if end_idx > start_idx:
                query = text[start_idx:end_idx].strip()
                if token_type == "WEB_SEARCH":
                    return await self._handle_web_search(query)
                elif token_type == "CODING":
                    return await self._handle_coding(query)
                elif token_type == "MIND_MAP":
                    return await self._handle_mind_map(query)
        return None

    async def process_message(
        self, message: ChatMessage, token: CancellationToken = None
    ) -> Response:
        """
        Process incoming messages and manage the reasoning flow.

        Args:
            message: Incoming chat message
            token: Cancellation token for the operation

        Returns:
            Response containing the reasoning result
        """
        iteration = 0
        current_reasoning = message.content
        collected_info: list[Response] = []

        while iteration < self.max_iterations and not (token and token.cancelled):
            # Process tokens in current reasoning
            for token_type in ["WEB_SEARCH", "CODING", "MIND_MAP"]:
                token_response = await self._process_token_in_text(current_reasoning, token_type)
                if token_response:
                    collected_info.append(token_response)

                    # Update reasoning with collected information
                    reasoning_msg = TextMessage(
                        content=f"Original Query: {message.content}\n"
                        f"Current Reasoning: {current_reasoning}\n"
                        f"New Information: {token_response.content}",
                        role="user",
                    )
                    response = await super().process_message(reasoning_msg, token)
                    current_reasoning = response.content

            # Check if reasoning is complete
            if "[COMPLETE]" in current_reasoning:
                break

            iteration += 1

        return Response(
            content=current_reasoning,
            metadata={
                "collected_information": [info.content for info in collected_info],
                "iterations": iteration,
            },
        )

    async def generate_response(
        self, messages: Sequence[LLMMessage], token: CancellationToken = None
    ) -> CreateResult:
        """
        Generate a response based on the message history.

        Args:
            messages: Sequence of messages in the conversation
            token: Cancellation token for the operation

        Returns:
            CreateResult containing the generated response
        """
        result = await super().generate_response(messages, token)

        # Add token usage information
        if not hasattr(result, "usage"):
            result.usage = RequestUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        return result
