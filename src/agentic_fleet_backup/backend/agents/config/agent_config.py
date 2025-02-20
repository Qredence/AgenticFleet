"""
Configuration management for AgenticFleet agents.

This module provides structured configuration and initialization for different agent types
and team compositions. It follows the Magentic-One best practices for agent configuration.
"""
from typing import Dict, List, Optional, Type

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Base configuration for all agents."""
    name: str
    role: str
    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None)
    streaming: bool = Field(default=True)

class TeamConfig(BaseModel):
    """Configuration for agent teams."""
    name: str
    description: str
    agents: List[AgentConfig]
    max_turns: int = Field(default=10)
    max_stalls: int = Field(default=3)

# Default configurations for different agent types
DEFAULT_WEB_SURFER_CONFIG = AgentConfig(
    name="web_surfer",
    role="Web research and information gathering agent",
    temperature=0.7,
)

DEFAULT_FILE_SURFER_CONFIG = AgentConfig(
    name="file_surfer",
    role="Local file system navigation and search agent",
    temperature=0.7,
)

DEFAULT_CODER_CONFIG = AgentConfig(
    name="magentic_one_coder",
    role="Code generation and modification specialist",
    temperature=0.8,
)

# Team configurations
MAGENTIC_FLEET_ONE_TEAM = TeamConfig(
    name="MagenticFleet One",
    description="Advanced team configuration for complex coding tasks",
    agents=[
        DEFAULT_WEB_SURFER_CONFIG,
        DEFAULT_FILE_SURFER_CONFIG,
        DEFAULT_CODER_CONFIG,
    ],
    max_turns=10,
)

WEBSEARCH_FLEET_TEAM = TeamConfig(
    name="WebSearch Fleet",
    description="Specialized team for web research tasks",
    agents=[
        DEFAULT_WEB_SURFER_CONFIG.copy(update={"temperature": 0.9}),
        DEFAULT_FILE_SURFER_CONFIG,
    ],
    max_turns=8,
)

# Registry of available team configurations
TEAM_REGISTRY: Dict[str, TeamConfig] = {
    "magentic_fleet_one": MAGENTIC_FLEET_ONE_TEAM,
    "websearch_fleet": WEBSEARCH_FLEET_TEAM,
}

def get_team_config(team_name: str) -> Optional[TeamConfig]:
    """Retrieve team configuration by name."""
    return TEAM_REGISTRY.get(team_name.lower())

def register_team_config(team_name: str, config: TeamConfig) -> None:
    """Register a new team configuration."""
    TEAM_REGISTRY[team_name.lower()] = config
