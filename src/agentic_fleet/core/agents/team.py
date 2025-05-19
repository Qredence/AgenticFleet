"""
Agent team initialization utilities for AgenticFleet.

This module provides functionality for initializing and managing agent teams.
Moved from agent_registry/__init__.py and consolidated here.
"""

from typing import Any

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor


def initialize_default_agents(model_client=None) -> list[AssistantAgent]:
    """
    Initialize the default set of agents, including the required executor agent.

    Args:
        model_client: The LLM client to use for agents that require it

    Returns:
        list of initialized agents
    """
    agents = [
        MagenticOneCoderAgent(name="coder", model_client=model_client),
        FileSurfer(name="file_surfer", model_client=model_client),
        MultimodalWebSurfer(name="web_surfer", model_client=model_client),
        CodeExecutorAgent(
            name="executor",
            code_executor=LocalCommandLineCodeExecutor(timeout=60),
            description="Executes code in a safe local environment.",
        ),
    ]
    return agents


def initialize_agent_team(
    team_config: dict[str, Any] | None = None, model_client=None
) -> list[AssistantAgent]:
    """
    Initialize a team of agents with specified configuration.

    Args:
        team_config: Optional configuration for the team
        model_client: The LLM client to use for agents that require it

    Returns:
        list of configured agents
    """
    agents = initialize_default_agents(model_client=model_client)

    if team_config:
        for agent in agents:
            agent_config = team_config.get(agent.name, {})
            for key, value in agent_config.items():
                setattr(agent, key, value)

    return agents
