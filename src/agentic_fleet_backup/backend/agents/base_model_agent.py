"""
Base model agent using Pydantic, following the general structure of AutoGen agents.
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel


class BaseModelAgent(BaseModel):
    """
    A base agent model that defines common fields and methods for specialized agents.
    This aligns with the structure of AutoGen-based agents but uses Pydantic
    for input validation and structured configuration.

    Fields:
        name: The name of the agent.
        role: The role of the agent (e.g., 'planner', 'researcher', 'implementer').
        system_prompt: The system prompt or instruction the agent should follow.
    """

    name: str
    role: Optional[str] = "base_agent"
    system_prompt: Optional[str] = "You are a generic base agent."

    class Config:
        arbitrary_types_allowed = True

    def run(self, user_input: str, **kwargs: Any) -> str:
        """
        A generic run method that processes user_input.
        In specialized agents, you can override this method
        with more specific logic.
        """
        logging.info(f"[BaseModelAgent] {self.name} (role={self.role}) received input: {user_input}")
        # Implement minimal placeholder logic:
        # In a real scenario, you could integrate with an LLM or other processing here.
        return f"BaseModelAgent {self.name} processed input: {user_input}"
