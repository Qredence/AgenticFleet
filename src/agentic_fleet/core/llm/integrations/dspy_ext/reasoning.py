"""
DSPy-Enhanced Reasoning Agent for AgenticFleet.

This module provides an Autogen-compatible agent that leverages DSPy's
reasoning capabilities while working with Azure OpenAI mini models.
"""

from typing import Any

from autogen_core import AssistantAgent
from autogen_ext.message import Message

from .compiler import AzureMiniCompiler
from .modules import ChainOfThoughtModule, ReflectionModule


class DSPyReasoningAgent(AssistantAgent):
    """
    An Autogen agent enhanced with DSPy reasoning capabilities.

    This agent combines Autogen's message handling with DSPy's structured
    reasoning, optimized for Azure OpenAI mini models.
    """

    def __init__(
        self,
        name: str,
        model_name: AzureMiniCompiler.SUPPORTED_MODELS,
        api_key: str,
        system_prompt: str | None = None,
        **kwargs,
    ):
        """
        Initialize the DSPy-enhanced reasoning agent.

        Args:
            name: Name of the agent
            model_name: Azure OpenAI model to use (o3-mini or gpt-4o-mini)
            api_key: Azure OpenAI API key
            system_prompt: Optional system prompt for the agent
            **kwargs: Additional configuration parameters
        """
        super().__init__(name=name, **kwargs)

        # Initialize DSPy compiler and modules
        self.compiler = AzureMiniCompiler(model_name=model_name, api_key=api_key, **kwargs)

        self.cot_module = ChainOfThoughtModule()
        self.reflection_module = ReflectionModule()

        # Compile modules with our specialized compiler
        self.cot_module = self.compiler.compile(self.cot_module)
        self.reflection_module = self.compiler.compile(self.reflection_module)

        self.system_prompt = system_prompt or self._default_system_prompt()

    async def process_message(
        self, message: Message, context: dict[str, Any] | None = None
    ) -> Message:
        """
        Process incoming messages using DSPy-enhanced reasoning.

        Args:
            message: The incoming message to process
            context: Optional context information

        Returns:
            A response message with enhanced reasoning
        """
        # Generate chain-of-thought reasoning
        cot_result = await self._generate_reasoning(message.content, context)

        # Reflect on the reasoning if needed
        if context and context.get("reflect", False):
            reflection = await self._reflect_on_reasoning(cot_result.reasoning_steps)

            # Incorporate reflection into response
            response_content = (
                f"Reasoning:\n{cot_result.reasoning_steps}\n\n"
                f"Conclusion:\n{cot_result.conclusion}\n\n"
                f"Reflection:\n{reflection.insights}\n\n"
                f"Suggested Improvements:\n{reflection.improvements}"
            )
        else:
            response_content = (
                f"Reasoning:\n{cot_result.reasoning_steps}\n\nConclusion:\n{cot_result.conclusion}"
            )

        return Message(role="assistant", content=response_content, name=self.name)

    async def _generate_reasoning(
        self, content: str, context: dict[str, Any] | None = None
    ) -> dspy.Prediction:
        """Generate chain-of-thought reasoning for the given content."""
        return self.cot_module(context=context or {}, question=content)

    async def _reflect_on_reasoning(
        self, reasoning: str, feedback: str | None = None
    ) -> dspy.Prediction:
        """Generate reflection on previous reasoning."""
        return self.reflection_module(reasoning=reasoning, feedback=feedback)

    def _default_system_prompt(self) -> str:
        """Get the default system prompt for the agent."""
        return """You are a reasoning agent that uses structured thinking to solve problems.
        Always break down complex problems into smaller steps and explain your thought process.
        Focus on clear, logical reasoning while being mindful of the constraints of the mini models."""
