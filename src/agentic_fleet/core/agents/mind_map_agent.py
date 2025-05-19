"""
Mind Map Agent Module.

This module implements an agent that constructs and analyzes knowledge graphs
to track logical relationships in complex reasoning chains.
"""

from collections.abc import Sequence
from typing import Any

from autogen_agentchat.messages import ChatMessage
from autogen_core import CancellationToken
from autogen_core.models import CreateResult, LLMMessage, RequestUsage
from pydantic import BaseModel

from agentic_fleet.core.agents.base import BaseAgent
from agentic_fleet.core.tools.mind_map.mind_map_tool import MindMapTool


class MindMapConfig(BaseModel):
    """Configuration for the Mind Map Agent."""

    graph_type: str = "directed"
    max_nodes: int = 50
    clustering_threshold: float = 0.7
    entity_extraction_temperature: float = 0.7
    relationship_extraction_temperature: float = 0.8


class MindMapAgent(BaseAgent):
    """
    Agent that constructs and analyzes knowledge graphs to track
    logical relationships in complex reasoning chains.
    """

    def __init__(
        self,
        name: str = "mind_map_agent",
        description: str = "",
        temperature: float = 0.5,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Mind Map Agent.

        Args:
            name: Name of the agent
            description: Description of the agent
            temperature: Temperature parameter for entity and relationship extraction
            **kwargs: Additional arguments passed to BaseChatAgent
        """
        # Extract model_client and system_message for BaseAgent's constructor
        model_client = kwargs.pop("model_client", None)
        system_message = kwargs.pop("system_message", self._get_default_system_message())

        super().__init__(
            name=name,
            description=description,
            model_client=model_client,
            system_message=system_message,
            **kwargs,
        )

        # Extract config from kwargs or use defaults
        # The 'config' kwarg might be a dict from load_component or an actual MindMapConfig object
        mind_map_specific_config_data = kwargs.get("config", {})
        if isinstance(mind_map_specific_config_data, MindMapConfig):
            self.mind_map_config = mind_map_specific_config_data
        else:
            self.mind_map_config = MindMapConfig(**mind_map_specific_config_data)

        self.mind_map_tool = MindMapTool(
            graph_type=self.mind_map_config.graph_type,
            max_nodes=self.mind_map_config.max_nodes,
            clustering_threshold=self.mind_map_config.clustering_threshold,
        )
        # self.config is used by BaseAgent for its AgentConfig. Let's keep specific config separate.
        # self.config = mind_map_config # This would overwrite BaseAgent.config
        self.temperature = temperature  # Retain for now, but ideally use model_client's temp or pass to generate_response

    async def process_message(
        self, message: str | ChatMessage, token: CancellationToken = None
    ) -> dict[str, Any]:
        """
        Process incoming messages and manage the mind map operations.

        Args:
            message: Incoming chat message or string
            token: Cancellation token for the operation

        Returns:
            Response containing the operation result
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

            if command == "construct":
                result = await self._construct_mind_map(
                    params.get("reasoning_chain", ""), params.get("context", {})
                )
                response_content = str(result)
            elif command == "insights":
                insights = await self._extract_insights(params.get("focus_area"))
                response_content = insights
            elif command == "recommendations":
                recommendations = await self._get_recommendations(
                    params.get("query", ""), params.get("context", {})
                )
                response_content = str(recommendations)
            elif command == "clear":
                self.mind_map_tool.clear_graph()
                response_content = "Mind map cleared successfully"
            else:
                response_content = f"Unknown command: {command}. Available commands: construct, insights, recommendations, clear"
                error = True

            return {"content": response_content, "error": error, "role": "assistant"}

        except Exception as e:
            return {
                "content": f"Error processing mind map operation: {str(e)}",
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
        # Use the generate_response from BaseAgent (which ultimately calls AssistantAgent.on_messages)
        # The temperature from self.temperature (init arg) or from specific config (e.g. entity_extraction_temperature)
        # should be passed here if needed for this specific LLM call.
        # If no temperature is passed, BaseAgent's model_client default will be used.
        current_temperature = temperature if temperature is not None else self.temperature

        # Ensure model_client exists, otherwise BaseAgent.generate_response will raise an error or use a mock if that's implemented
        if not self.model_client:
            # This case should be handled by BaseAgent's generate_response, but as a safeguard:
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

        # Call the superclass method from BaseAgent, which handles the actual LLM call
        # BaseAgent.generate_response expects List[ChatMessage], LLMMessage is compatible
        create_result = await super().generate_response(
            messages=messages, token=token, temperature=current_temperature
        )

        # Ensure usage is part of the result, as the original code did
        if not hasattr(create_result, "usage") or create_result.usage is None:
            create_result.usage = RequestUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        return create_result

    async def _construct_mind_map(
        self, reasoning_chain: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Construct a mind map from a reasoning chain.

        Args:
            reasoning_chain: Text containing the reasoning process
            context: Optional context information

        Returns:
            Dictionary containing the constructed mind map
        """
        try:
            # Extract entities
            entities_data_str = await self._extract_entities(
                reasoning_chain, self.mind_map_config.entity_extraction_temperature
            )
            # Assuming _extract_entities now returns a string that needs parsing, or MindMapTool is updated
            # For now, let's assume MindMapTool.add_entities can handle the string directly or it's parsed before calling
            self.mind_map_tool.add_entities(
                entities_data_str
            )  # This might need adjustment based on _extract_entities return type

            # Extract relationships
            relationships_data_str = await self._extract_relationships(
                reasoning_chain, self.mind_map_config.relationship_extraction_temperature
            )
            self.mind_map_tool.add_relationships(
                relationships_data_str
            )  # Similar adjustment might be needed

            return self.mind_map_tool.get_graph_state()

        except Exception as e:
            raise RuntimeError(f"Error constructing mind map: {str(e)}")

    async def _extract_insights(self, focus_area: str | None = None) -> str:
        """
        Extract insights from the current mind map.

        Args:
            focus_area: Optional area to focus analysis on

        Returns:
            String containing extracted insights
        """
        try:
            analysis = self.mind_map_tool.analyze_graph()
            messages = [
                LLMMessage(role="system", content="Extract key insights from the graph analysis."),
                LLMMessage(role="user", content=f"Analysis: {analysis}\nFocus Area: {focus_area}"),
            ]
            result = await self.generate_response(messages, temperature=self.temperature)
            return result.message.content

        except Exception as e:
            raise RuntimeError(f"Error extracting insights: {str(e)}")

    async def _get_recommendations(
        self, query: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get strategic recommendations based on the mind map.

        Args:
            query: Query to focus recommendations on
            context: Optional context information

        Returns:
            List of recommendation objects
        """
        try:
            graph_state = self.mind_map_tool.get_graph_state()
            messages = [
                LLMMessage(
                    role="system",
                    content="Generate strategic recommendations based on the mind map.",
                ),
                LLMMessage(
                    role="user",
                    content=f"Query: {query}\nGraph State: {graph_state}\nContext: {context}",
                ),
            ]
            result = await self.generate_response(messages, temperature=self.temperature)
            return self._parse_recommendations(result.message.content)

        except Exception as e:
            raise RuntimeError(f"Error generating recommendations: {str(e)}")

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
                params = {"content": param_text}

        return command, params

    async def _extract_entities(self, text: str, temperature: float) -> str:
        """Extract entities from text using LLM."""
        messages = [
            LLMMessage(
                role="system", content="Extract key entities from the text. Format as JSON."
            ),
            LLMMessage(role="user", content=text),
        ]
        result = await self.generate_response(messages, temperature=temperature)
        return result.message.content

    async def _extract_relationships(self, text: str, temperature: float) -> str:
        """Extract relationships from text using LLM."""
        messages = [
            LLMMessage(
                role="system", content="Extract relationships between entities. Format as JSON."
            ),
            LLMMessage(role="user", content=text),
        ]
        result = await self.generate_response(messages, temperature=temperature)
        return result.message.content

    def _parse_recommendations(self, text: str) -> list[dict[str, Any]]:
        """Parse recommendations from LLM response."""
        try:
            import json

            return json.loads(text)
        except json.JSONDecodeError:
            return [{"error": "Failed to parse recommendations"}]

    def _get_default_system_message(self) -> str:
        return "You are a Mind Map agent. You construct and analyze knowledge graphs to track logical relationships."

    def _get_default_description(self) -> str:
        return "An agent that creates and analyzes mind maps from text."

    def dump_component(self) -> dict[str, Any]:
        """Dump the agent configuration to a dictionary format."""
        base_dump = super().dump_component()
        # Add MindMapConfig to the dump
        base_dump["config"]["mind_map_specific_config"] = self.mind_map_config.model_dump()
        # The 'model' field in base_dump["config"] is already handled by BaseAgent
        return base_dump

    def produced_message_types(self) -> list[str]:
        """
        Get the types of messages this agent can produce.

        Returns:
            List[str]: List of supported message types
        """
        # Returns "text" for general chat, and potentially a custom type for structured mind map data if applicable
        return ["text", "mind_map_data"]

    @classmethod
    def load_component(cls, config_dict: dict[str, Any]) -> "MindMapAgent":
        """Load an agent from a configuration dictionary."""
        agent_config_data = config_dict.get("config", {})

        # Extract MindMap specific config if it exists
        mind_map_specific_config_data = agent_config_data.pop("mind_map_specific_config", {})

        # The actual model_client is not part of dump/load, it's injected at runtime.
        # We will pass the config for mind_map_config through kwargs.
        # model_client is injected at runtime by the agent creation mechanism (e.g., registry or factory)
        # The __init__ method of MindMapAgent is now designed to pick up mind_map_specific_config_data from the 'config' kwarg.
        return cls(
            name=agent_config_data.get("name", "mind_map_agent"),
            description=agent_config_data.get("description"),
            system_message=agent_config_data.get("system_message"),
            model_client=None,  # Placeholder, to be injected by the factory/registry
            config=mind_map_specific_config_data,  # Pass the dict for MindMapConfig specific fields
        )
