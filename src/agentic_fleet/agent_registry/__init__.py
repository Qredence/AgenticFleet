"""Agent registry module for AgenticFleet.

This module provides functionality for initializing and managing agent teams.
"""

from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer


def initialize_default_agents() -> list[AssistantAgent]:
    """
    Initialize the default set of agents.

    Returns:
        List of initialized agents
    """
    agents = [
        MagenticOneCoderAgent(name="coder"),
        FileSurfer(name="file_surfer"),
        MultimodalWebSurfer(name="web_surfer"),
    ]
    return agents


def initialize_agent_team(team_config: dict[str, Any] | None = None) -> list[AssistantAgent]:
    """
    Initialize a team of agents with specified configuration.

    Args:
        team_config: Optional configuration for the team

    Returns:
        List of configured agents
    """
    agents = initialize_default_agents()

    if team_config:
        for agent in agents:
            agent_config = team_config.get(agent.name, {})
            for key, value in agent_config.items():
                setattr(agent, key, value)

    return agents
