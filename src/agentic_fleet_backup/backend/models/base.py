"""Base classes and interfaces for model clients."""

from typing import Any, Dict, Optional, AsyncGenerator
from abc import ABC, abstractmethod


class BaseModelInfo:
    """Model capabilities information.

    Attributes:
        vision: Whether the model supports vision/image processing
        function_calling: Whether the model supports function calling
        json_output: Whether the model can output structured JSON
        family: The model family/provider name
    """
    def __init__(self,
                 vision: bool = False,
                 function_calling: bool = False,
                 json_output: bool = False,
                 family: str = "unknown"):
        self.vision = vision
        self.function_calling = function_calling
        self.json_output = json_output
        self.family = family

    def to_dict(self) -> Dict[str, Any]:
        """Convert model info to dictionary format."""
        return {
            "vision": self.vision,
            "function_calling": self.function_calling,
            "json_output": self.json_output,
            "family": self.family
        }

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access to model info attributes."""
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        """Check if an attribute exists."""
        return hasattr(self, key)


class BaseProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        pass
