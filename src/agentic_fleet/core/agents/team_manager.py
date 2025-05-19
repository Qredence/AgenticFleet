"""
Team manager for coordinating agent teams in AgenticFleet.

This module provides functionality for managing teams of agents, including:
- Team initialization and configuration
- Agent registration and coordination
- Team execution monitoring
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from autogen_core.models import ChatCompletionClient
from pydantic import BaseModel

from agentic_fleet.core.agents.base import BaseAgent
from agentic_fleet.core.agents.orchestrator import Orchestrator, OrchestratorConfig

logger = logging.getLogger(__name__)


class TeamConfig(BaseModel):
    """Configuration for an agent team."""

    name: str
    description: str | None = None
    orchestrator_config: OrchestratorConfig | None = None
    max_parallel_tasks: int = 1
    max_retries: int = 3
    timeout_seconds: int = 3600  # 1 hour default timeout


@dataclass
class TeamMetrics:
    """Metrics for team performance tracking."""

    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_task_time: float = 0.0


class TeamManager:
    """
    Manages teams of agents and their coordination.

    The team manager:
    1. Initializes and configures agent teams
    2. Handles agent registration and coordination
    3. Monitors team execution and performance
    4. Provides metrics and status reporting
    """

    def __init__(
        self,
        config: TeamConfig,
        model_client: ChatCompletionClient | None = None,
    ) -> None:
        """Initialize the team manager.

        Args:
            config: Team configuration
            model_client: The LLM client to use
        """
        self.config = config
        self.model_client = model_client

        # Initialize collections
        self.agents: dict[str, BaseAgent] = {}
        self.orchestrator: Orchestrator | None = None
        self.metrics = TeamMetrics()

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """Register an agent with the team.

        Args:
            name: Name to register the agent under
            agent: The agent instance to register
        """
        if name in self.agents:
            logger.warning(f"Overwriting existing agent registration for {name}")
        self.agents[name] = agent

        # Update orchestrator's available agents if it exists
        if self.orchestrator:
            self.orchestrator.available_agents = self.agents

    def register_agents(self, agents: dict[str, BaseAgent]) -> None:
        """Register multiple agents at once.

        Args:
            agents: Dictionary of agent names to instances
        """
        for name, agent in agents.items():
            self.register_agent(name, agent)

    def initialize_orchestrator(
        self, name: str = "orchestrator", config: OrchestratorConfig | None = None
    ) -> None:
        """Initialize the team's orchestrator agent.

        Args:
            name: Name for the orchestrator
            config: Optional custom configuration
        """
        orchestrator_config = config or self.config.orchestrator_config or OrchestratorConfig()

        self.orchestrator = Orchestrator(
            name=name,
            config=orchestrator_config,
            model_client=self.model_client,
            available_agents=self.agents,
        )

    async def execute_task(self, task: str) -> Any:
        """Execute a task using the team.

        Args:
            task: The task to execute

        Returns:
            The task execution results

        Raises:
            RuntimeError: If no orchestrator is initialized
        """
        if not self.orchestrator:
            raise RuntimeError("No orchestrator initialized. Call initialize_orchestrator() first.")

        try:
            import time

            start_time = time.time()

            # Execute task through orchestrator
            results = await self.orchestrator.execute_task(task)

            # Update metrics
            execution_time = time.time() - start_time
            self.metrics.tasks_completed += 1
            self.metrics.total_execution_time += execution_time
            self.metrics.average_task_time = (
                self.metrics.total_execution_time / self.metrics.tasks_completed
            )

            return results

        except Exception as e:
            self.metrics.tasks_failed += 1
            logger.error(f"Task execution failed: {str(e)}")
            raise

    def get_metrics(self) -> TeamMetrics:
        """Get current team performance metrics.

        Returns:
            Current team metrics
        """
        return self.metrics

    def get_agent_status(self) -> dict[str, str]:
        """Get status of all registered agents.

        Returns:
            Dictionary of agent names to their current status
        """
        status = {}
        for name, agent in self.agents.items():
            # Get agent status if it has a status property, otherwise mark as 'unknown'
            status[name] = getattr(agent, "status", "unknown")
        return status

    async def cleanup(self) -> None:
        """Clean up team resources."""
        for agent in self.agents.values():
            if hasattr(agent, "cleanup") and callable(agent.cleanup):
                try:
                    if asyncio.iscoroutinefunction(agent.cleanup):
                        await agent.cleanup()
                    else:
                        agent.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up agent {agent.name}: {str(e)}")
