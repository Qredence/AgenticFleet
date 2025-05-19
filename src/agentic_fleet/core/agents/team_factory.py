"""
Team factory for creating agent teams in AgenticFleet.

This module provides factory methods for creating different types of agent teams
with various configurations and specializations.
"""

import logging
from typing import Any

from autogen_core.models import ChatCompletionClient
from pydantic import BaseModel

from agentic_fleet.core.agents.base import BaseAgent
from agentic_fleet.core.agents.orchestrator import OrchestratorConfig
from agentic_fleet.core.agents.team_manager import TeamConfig, TeamManager

logger = logging.getLogger(__name__)


class TeamSpecialization(BaseModel):
    """Configuration for team specialization."""

    name: str
    description: str
    required_agents: list[str]
    orchestrator_config: OrchestratorConfig | None = None
    team_config: dict[str, Any] | None = None


class TeamFactory:
    """
    Factory for creating specialized agent teams.

    This factory:
    1. Provides predefined team configurations
    2. Creates teams with specific specializations
    3. Validates team compositions
    4. Configures team-specific settings
    """

    def __init__(self, model_client: ChatCompletionClient | None = None):
        """Initialize the team factory.

        Args:
            model_client: The LLM client to use for created teams
        """
        self.model_client = model_client
        self._specializations: dict[str, TeamSpecialization] = {}
        self._register_default_specializations()

    def _register_default_specializations(self) -> None:
        """Register default team specializations."""
        self._specializations.update(
            {
                "coding": TeamSpecialization(
                    name="coding",
                    description="Team specialized in software development tasks",
                    required_agents=["coder", "file_surfer", "executor"],
                    orchestrator_config=OrchestratorConfig(
                        planning_temperature=0.7, max_steps=30, stall_threshold_seconds=180
                    ),
                    team_config={
                        "max_parallel_tasks": 1,
                        "max_retries": 3,
                        "timeout_seconds": 1800,  # 30 minutes
                    },
                ),
                "research": TeamSpecialization(
                    name="research",
                    description="Team specialized in web research and information gathering",
                    required_agents=["web_surfer", "file_surfer"],
                    orchestrator_config=OrchestratorConfig(
                        planning_temperature=0.8, max_steps=20, stall_threshold_seconds=240
                    ),
                    team_config={
                        "max_parallel_tasks": 2,
                        "max_retries": 2,
                        "timeout_seconds": 2400,  # 40 minutes
                    },
                ),
                "general": TeamSpecialization(
                    name="general",
                    description="Balanced team for general-purpose tasks",
                    required_agents=["web_surfer", "file_surfer", "coder", "executor"],
                    orchestrator_config=OrchestratorConfig(
                        planning_temperature=0.7, max_steps=40, stall_threshold_seconds=300
                    ),
                    team_config={
                        "max_parallel_tasks": 1,
                        "max_retries": 3,
                        "timeout_seconds": 3600,  # 1 hour
                    },
                ),
            }
        )

    def register_specialization(self, specialization: TeamSpecialization) -> None:
        """Register a new team specialization.

        Args:
            specialization: The specialization configuration to register
        """
        self._specializations[specialization.name] = specialization

    def get_specialization(self, name: str) -> TeamSpecialization | None:
        """Get a registered specialization by name.

        Args:
            name: Name of the specialization to retrieve

        Returns:
            The specialization configuration if found, None otherwise
        """
        return self._specializations.get(name)

    def list_specializations(self) -> list[str]:
        """List all registered specialization names.

        Returns:
            List of specialization names
        """
        return list(self._specializations.keys())

    def create_team(
        self,
        specialization: str,
        available_agents: dict[str, BaseAgent],
        custom_config: dict[str, Any] | None = None,
    ) -> TeamManager:
        """Create a team with the specified specialization.

        Args:
            specialization: Name of the specialization to use
            available_agents: Dictionary of available agents to use
            custom_config: Optional custom configuration to override defaults

        Returns:
            Configured TeamManager instance

        Raises:
            ValueError: If specialization not found or required agents missing
        """
        # Get specialization config
        spec = self._specializations.get(specialization)
        if not spec:
            raise ValueError(f"Unknown specialization: {specialization}")

        # Validate required agents
        missing_agents = [agent for agent in spec.required_agents if agent not in available_agents]
        if missing_agents:
            raise ValueError(
                f"Missing required agents for {specialization} specialization: "
                f"{', '.join(missing_agents)}"
            )

        # Create team configuration
        team_config = TeamConfig(
            name=f"{specialization}_team",
            description=spec.description,
            orchestrator_config=spec.orchestrator_config,
            **{**spec.team_config, **(custom_config or {})},
        )

        # Create and configure team
        team = TeamManager(config=team_config, model_client=self.model_client)

        # Register required agents
        required_agent_dict = {
            name: agent for name, agent in available_agents.items() if name in spec.required_agents
        }
        team.register_agents(required_agent_dict)

        # Initialize orchestrator
        team.initialize_orchestrator(
            name=f"{specialization}_orchestrator", config=spec.orchestrator_config
        )

        return team

    def create_custom_team(
        self,
        name: str,
        description: str,
        agents: dict[str, BaseAgent],
        orchestrator_config: OrchestratorConfig | None = None,
        team_config: dict[str, Any] | None = None,
    ) -> TeamManager:
        """Create a custom team with specified configuration.

        Args:
            name: Name for the team
            description: Team description
            agents: Dictionary of agents to include
            orchestrator_config: Optional orchestrator configuration
            team_config: Optional team configuration

        Returns:
            Configured TeamManager instance
        """
        config = TeamConfig(
            name=name,
            description=description,
            orchestrator_config=orchestrator_config,
            **(team_config or {}),
        )

        team = TeamManager(config=config, model_client=self.model_client)

        team.register_agents(agents)
        team.initialize_orchestrator(name=f"{name}_orchestrator", config=orchestrator_config)

        return team
