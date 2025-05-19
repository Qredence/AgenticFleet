# src/agentic_fleet/core/agents/registry.py
"""Agent registry for AgenticFleet."""

from typing import Dict, List, Optional, Type

from agentic_fleet.core.agents.base import BaseAgent


class AgentRegistry:
    """Registry for agent types."""

    def __init__(self):
        """Initialize the agent registry."""
        self._agent_types: Dict[str, Type[BaseAgent]] = {}

    def register(self, agent_type: str, agent_cls: Type[BaseAgent]) -> None:
        """Register an agent type.

        Args:
            agent_type: Type identifier for the agent
            agent_cls: Agent class
        """
        if agent_type in self._agent_types:
            raise ValueError(f"Agent type '{agent_type}' already registered")

        self._agent_types[agent_type] = agent_cls

    def get(self, agent_type: str) -> Optional[Type[BaseAgent]]:
        """Get an agent class by type.

        Args:
            agent_type: Type identifier for the agent

        Returns:
            Agent class or None if not found
        """
        return self._agent_types.get(agent_type)

    def list_types(self) -> List[str]:
        """List all registered agent types.

        Returns:
            List of agent type identifiers
        """
        return list(self._agent_types.keys())

    def create(self, agent_type: str, **kwargs) -> BaseAgent:
        """Create an agent instance.

        Args:
            agent_type: Type identifier for the agent
            **kwargs: Additional arguments for the agent constructor

        Returns:
            Agent instance

        Raises:
            ValueError: If the agent type is not registered
        """
        agent_cls = self.get(agent_type)
        if agent_cls is None:
            raise ValueError(f"Agent type '{agent_type}' not registered")

        return agent_cls(**kwargs)


# Create singleton instance
agent_registry = AgentRegistry()

# Register built-in agent types
from agentic_fleet.core.agents.coder import CoderAgent
from agentic_fleet.core.agents.file_surfer import FileSurferAgent
from agentic_fleet.core.agents.orchestrator import OrchestratorAgent
from agentic_fleet.core.agents.web_surfer import WebSurferAgent

agent_registry.register("coder", CoderAgent)
agent_registry.register("file_surfer", FileSurferAgent)
agent_registry.register("orchestrator", OrchestratorAgent)
agent_registry.register("web_surfer", WebSurferAgent)
