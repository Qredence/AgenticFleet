"""Client implementation for Ollama API integration.

This module provides a client for interacting with locally hosted Ollama models
through their API endpoint. It supports both streaming and non-streaming responses,
with proper error handling and async capabilities.
"""

import json
import logging
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from autogen_core.models import LLMMessage as Message, UserMessage

from agentic_fleet.backend.models.base import BaseModelInfo, BaseProvider

logger = logging.getLogger(__name__)


class OllamaModels(str, Enum):
    """Supported Ollama models."""

    LLAMA2 = "llama2"
    CODELLAMA = "codellama"
    MISTRAL = "mistral"
    MIXTRAL = "mixtral"
    LLAVA = "llava"
    GEMMA = "gemma"


class OllamaClient(BaseProvider):
    """Client for interacting with Ollama API.

    This client provides access to locally hosted Ollama models through their API endpoint.
    It supports:
    - Multiple model variants
    - Streaming responses
    - Custom model parameters
    - Proper error handling
    - Async operations
    """

    def __init__(
        self,
        model: str = OllamaModels.LLAMA2.value,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model_info: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Ollama client.

        Args:
            model: Model identifier (e.g., "llama2", "codellama")
            base_url: Ollama API base URL
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model_info: Model capabilities information
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.model_info = model_info or BaseModelInfo(
            vision=model == OllamaModels.LLAVA.value,
            function_calling=True,
            json_output=True,
            family="ollama"
        )

        # Validate model availability
        if not self._is_valid_model(model):
            raise ValueError(f"Model {model} is not a recognized Ollama model")

    @staticmethod
    def _is_valid_model(model: str) -> bool:
        """Check if the model is supported by Ollama."""
        try:
            return model in [m.value for m in OllamaModels]
        except ValueError:
            return False

    def _format_messages(self, messages: List[Message]) -> str:
        """Format messages for Ollama API.

        Args:
            messages: List of Message objects

        Returns:
            Formatted prompt string
        """
        formatted = []
        for msg in messages:
            role = "user" if isinstance(msg, UserMessage) else "assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    async def generate(self, prompt: Union[str, List[Message]], **kwargs: Any) -> str:
        """Generate a response from the model.

        Args:
            prompt: Input prompt or list of messages
            **kwargs: Additional parameters for the API call

        Returns:
            Generated response text

        Raises:
            ConnectionError: If unable to connect to Ollama server
            Exception: For other API errors
        """
        if isinstance(prompt, list):
            prompt = self._format_messages(prompt)

        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": False,
        }

        if self.max_tokens:
            data["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {error_text}")

                    result = await response.json()
                    return result["response"]

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            raise ConnectionError(f"Unable to connect to Ollama server at {self.base_url}") from e
        except Exception as e:
            logger.error(f"Error during Ollama API call: {e}")
            raise

    async def stream(
        self, prompt: Union[str, List[Message]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream responses from the model.

        Args:
            prompt: Input prompt or list of messages
            **kwargs: Additional parameters for the API call

        Yields:
            Generated response text chunks

        Raises:
            ConnectionError: If unable to connect to Ollama server
            Exception: For other API errors
        """
        if isinstance(prompt, list):
            prompt = self._format_messages(prompt)

        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True,
        }

        if self.max_tokens:
            data["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {error_text}")

                    async for line in response.content:
                        if line:
                            try:
                                result = json.loads(line)
                                if "response" in result:
                                    yield result["response"]
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse streaming response: {line}")

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Ollama server: {e}")
            raise ConnectionError(f"Unable to connect to Ollama server at {self.base_url}") from e
        except Exception as e:
            logger.error(f"Error during Ollama API streaming: {e}")
            raise


# Example usage
if __name__ == "__main__":
    import asyncio

    client = OllamaClient(model="llama3.2", base_url="http://localhost:11434")

    async def main():
        response = await client.generate(
            [UserMessage(content="What is the capital of France?", source="user")]
        )
        print(response)

    asyncio.run(main())
