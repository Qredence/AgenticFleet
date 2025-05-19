"""
Web Search Agent Module.

This module implements an agent that performs web searches and analyzes
results to provide relevant information for the reasoning process.
"""

from collections.abc import Sequence
from typing import Any

from autogen_agentchat.messages import ChatMessage
from autogen_core import CancellationToken
from autogen_core.models import CreateResult, LLMMessage, RequestUsage
from pydantic import BaseModel

from agentic_fleet.core.agents.base import BaseAgent
from agentic_fleet.core.tools.web_search.web_search_tool import SearchResult, WebSearchTool


class WebSearchConfig(BaseModel):
    """Configuration for the Web Search Agent."""

    max_results: int = 5
    min_relevance_score: float = 0.7
    analysis_temperature: float = 0.7
    synthesis_temperature: float = 0.8


class WebSearchAgent(BaseAgent):
    """
    Agent that performs web searches and analyzes results to provide
    relevant information for the reasoning process.
    """

    def __init__(
        self,
        name: str = "web_search_agent",
        description: str = "",
        temperature: float = 0.6,
        **kwargs,
    ) -> None:
        """
        Initialize the Web Search Agent.

        Args:
            name: Name of the agent
            description: Description of the agent
            temperature: Temperature for the agent
            **kwargs: Additional arguments passed to BaseChatAgent
        """
        model_client = kwargs.pop("model_client", None)
        system_message = kwargs.pop("system_message", self._get_default_system_message())
        super().__init__(
            name=name,
            description=description,
            model_client=model_client,
            system_message=system_message,
            **kwargs,
        )

        self.temperature = (
            temperature  # General temperature, can be overridden by specific config values
        )

        # Extract config from kwargs or use defaults
        web_search_specific_config_data = kwargs.get("config", {})
        if isinstance(web_search_specific_config_data, WebSearchConfig):
            self.web_search_config = web_search_specific_config_data
        else:
            self.web_search_config = WebSearchConfig(**web_search_specific_config_data)

        self.web_search_tool = WebSearchTool(
            max_results=self.web_search_config.max_results,
            min_relevance_score=self.web_search_config.min_relevance_score,
        )
        # self.config is BaseAgent's AgentConfig. We store specific config in self.web_search_config

    async def process_message(
        self, message: str | ChatMessage, token: CancellationToken = None
    ) -> dict[str, Any]:
        """
        Process incoming messages and manage web search operations.

        Args:
            message: Incoming chat message or string
            token: Cancellation token for the operation

        Returns:
            Response containing the search and analysis results
        """
        if isinstance(message, str):
            message_content = message
        elif hasattr(message, "content"):
            message_content = message.content
        else:
            return {"content": "Invalid message type", "error": True, "role": "assistant"}

        try:
            # Parse the command and parameters from the message
            command, params = self._parse_message(message_content)
            response_content = ""
            error = False

            if command == "search":
                results = await self._perform_search(
                    params.get("query", ""), params.get("context", {})
                )
                response_content = str(results)
            elif command == "analyze":
                analysis = await self._analyze_results(
                    params.get("results", []), params.get("focus", None)
                )
                response_content = analysis
            elif command == "synthesize":
                synthesis = await self._synthesize_information(
                    params.get("query", ""), params.get("context", {})
                )
                response_content = synthesis
            else:
                response_content = (
                    f"Unknown command: {command}. Available commands: search, analyze, synthesize"
                )
                error = True

            return {"content": response_content, "error": error, "role": "assistant"}

        except Exception as e:
            return {
                "content": f"Error processing web search operation: {str(e)}",
                "error": True,
                "role": "assistant",
            }

    async def generate_response(
        self,
        messages: Sequence[LLMMessage],
        token: CancellationToken = None,
        temperature: float | None = None,
    ) -> CreateResult:
        """
        Generate a response based on the message history.

        Args:
            messages: Sequence of messages in the conversation
            token: Cancellation token for the operation
            temperature: Optional temperature for this specific call

        Returns:
            CreateResult containing the generated response
        """
        # Use the generate_response from BaseAgent
        current_temperature = temperature if temperature is not None else self.temperature

        if not self.model_client:
            mock_message = LLMMessage(
                content="Mock response - model_client not available", source="assistant"
            )
            return CreateResult(
                message=mock_message,
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                finish_reason="stop",
                content=mock_message.content,
                cached=False,
            )

        create_result = await super().generate_response(
            messages=messages, token=token, temperature=current_temperature
        )

        # Add token usage information
        if not hasattr(create_result, "usage") or create_result.usage is None:
            create_result.usage = RequestUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        return create_result

    async def _perform_search(
        self, query: str, context: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        """
        Perform a web search and return relevant results.

        Args:
            query: Search query
            context: Optional context to refine the search

        Returns:
            List of search results
        """
        try:
            # Refine the query using context if available
            if context:
                refined_query = await self._refine_query(query, context)
            else:
                refined_query = query

            # Perform the search
            results = await self.web_search_tool.search(refined_query)

            # Filter results by relevance
            filtered_results = [
                result
                for result in results
                if result.relevance_score >= self.web_search_config.min_relevance_score
            ]

            return filtered_results[: self.web_search_config.max_results]

        except Exception as e:
            raise RuntimeError(f"Error performing web search: {str(e)}")

    async def _analyze_results(
        self, results: list[SearchResult], focus: str | None = None
    ) -> str:
        """
        Analyze search results to extract key information.

        Args:
            results: List of search results to analyze
            focus: Optional focus area for analysis

        Returns:
            Analysis of the search results
        """
        try:
            # Create messages for analysis
            messages = [
                LLMMessage(
                    role="system", content="Analyze the search results and extract key information."
                ),
                LLMMessage(role="user", content=f"Results: {results}\nFocus Area: {focus}"),
            ]

            result = await self.generate_response(
                messages, temperature=self.web_search_config.analysis_temperature
            )
            return result.message.content

        except Exception as e:
            raise RuntimeError(f"Error analyzing search results: {str(e)}")

    async def _synthesize_information(
        self, query: str, context: dict[str, Any] | None = None
    ) -> str:
        """
        Synthesize information from search results into a coherent response.

        Args:
            query: Original search query
            context: Optional context for synthesis

        Returns:
            Synthesized information
        """
        try:
            # Perform search
            results = await self._perform_search(query, context)

            # Analyze results
            analysis = await self._analyze_results(results)

            # Create messages for synthesis
            messages = [
                LLMMessage(
                    role="system",
                    content="Synthesize the analyzed information into a coherent response.",
                ),
                LLMMessage(
                    role="user", content=f"Query: {query}\nAnalysis: {analysis}\nContext: {context}"
                ),
            ]

            result = await self.generate_response(
                messages, temperature=self.web_search_config.synthesis_temperature
            )
            return result.message.content

        except Exception as e:
            raise RuntimeError(f"Error synthesizing information: {str(e)}")

    async def _refine_query(self, query: str, context: dict[str, Any]) -> str:
        """
        Refine a search query using context information.

        Args:
            query: Original search query
            context: Context information for refinement

        Returns:
            Refined search query
        """
        try:
            messages = [
                LLMMessage(
                    role="system", content="Refine the search query using the provided context."
                ),
                LLMMessage(role="user", content=f"Query: {query}\nContext: {context}"),
            ]
            result = await self.generate_response(
                messages, temperature=self.temperature
            )  # Using general agent temperature
            return result.message.content

        except Exception as e:
            raise RuntimeError(f"Error refining query: {str(e)}")

    def _parse_message(self, content: str) -> tuple[str, dict[str, Any]]:
        """
        Parse the command and parameters from a message.

        Args:
            content: Message content to parse

        Returns:
            Tuple of (command, parameters)
        """
        # Simple parsing - could be enhanced based on needs
        parts = content.split(maxsplit=1)
        command = parts[0].lower()
        params = {}

        if len(parts) > 1:
            # Parse parameters from the rest of the message
            param_text = parts[1]
            try:
                import json

                params = json.loads(param_text)
            except json.JSONDecodeError:
                params = {"query": param_text}  # Default to query for search like agents

        return command, params

    # Methods to be kept from original if they don't conflict with BaseAgent
    # or if BaseAgent doesn't provide equivalents.
    async def on_reset(self) -> None:
        """Reset the agent's state."""
        # If BaseAgent has on_reset, call it.
        if hasattr(super(), "on_reset"):
            await super().on_reset()
        # Add any WebSearchAgent specific reset logic here if needed
        pass

    def produced_message_types(self) -> list[str]:
        """
        Get the types of messages this agent can produce.

        Returns:
            List[str]: List of supported message types
        """
        return ["text", "search_results"]

    def _get_default_system_message(self) -> str:
        return "You are a Web Search agent. You perform web searches and analyze results."

    def _get_default_description(self) -> str:
        return "An agent that performs web searches and synthesizes information."

    def dump_component(self) -> dict[str, Any]:
        """Dump the agent configuration to a dictionary format."""
        base_dump = super().dump_component()
        base_dump["config"]["web_search_specific_config"] = self.web_search_config.model_dump()
        return base_dump

    @classmethod
    def load_component(cls, config_dict: dict[str, Any]) -> "WebSearchAgent":
        """Load an agent from a configuration dictionary."""
        agent_config_data = config_dict.get("config", {})
        web_search_specific_config_data = agent_config_data.pop("web_search_specific_config", {})

        return cls(
            name=agent_config_data.get("name", "web_search_agent"),
            description=agent_config_data.get("description"),
            system_message=agent_config_data.get("system_message"),
            model_client=None,  # To be injected by factory/registry
            config=web_search_specific_config_data,
        )
