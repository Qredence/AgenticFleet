"""
Reasoning Package Initialization.

This package provides the implementation of the iterative retrieval-and-reasoning pattern,
which enables dynamic interaction between a main reasoning LLM and specialized agents
through token-based triggers.
"""

from typing import Any

from agentic_fleet.core.agents.coding_agent import CodingAgent
from agentic_fleet.core.agents.mind_map_agent import MindMapAgent
from agentic_fleet.core.agents.web_search_agent import WebSearchAgent

from .retrieval_reasoning import RetrievalReasoningOrchestrator


async def create_reasoning_orchestrator(config: dict[str, Any]) -> RetrievalReasoningOrchestrator:
    """
    Create and initialize a RetrievalReasoningOrchestrator with all required agents.

    Args:
        config: Configuration dictionary containing settings for agents

    Returns:
        Initialized RetrievalReasoningOrchestrator instance
    """
    # Initialize specialized agents
    mind_map_agent = MindMapAgent(name="mind_map_agent", **config.get("mind_map_config", {}))

    web_search_agent = WebSearchAgent(
        name="web_search_agent", **config.get("web_search_config", {})
    )

    coding_agent = CodingAgent(name="coding_agent", **config.get("coding_config", {}))

    # Create and return the orchestrator
    return RetrievalReasoningOrchestrator(
        name="retrieval_reasoning_orchestrator",
        mind_map_agent=mind_map_agent,
        web_search_agent=web_search_agent,
        coding_agent=coding_agent,
        max_iterations=config.get("max_iterations", 5),
        llm_config=config.get("llm_config", {}),
    )


__all__ = ["RetrievalReasoningOrchestrator", "create_reasoning_orchestrator"]
