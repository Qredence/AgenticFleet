"""
DSPy Modules for AgenticFleet.

This module provides specialized DSPy modules for reasoning tasks,
optimized for Azure OpenAI mini models.
"""


import dspy
from dspy import InputField, OutputField


class ChainOfThoughtModule(dspy.Module):
    """Module for generating detailed chain-of-thought reasoning."""

    input_context = InputField(desc="Context or situation to reason about")
    input_question = InputField(desc="Specific question or problem to address")

    reasoning_steps = OutputField(desc="Step-by-step reasoning process")
    conclusion = OutputField(desc="Final conclusion based on reasoning")

    def forward(self, context: str, question: str) -> dspy.Prediction:
        """
        Generate chain-of-thought reasoning for a given context and question.

        Args:
            context: The context or situation to reason about
            question: The specific question or problem to address

        Returns:
            A prediction containing reasoning steps and conclusion
        """
        prompt = dspy.ChainOfThought(
            f"""
            Context: {context}
            Question: {question}

            Let's approach this step by step:
            1) First, let's identify the key elements...
            2) Then, analyze their relationships...
            3) Finally, draw a logical conclusion...

            Reasoning steps should be clear and concise.
            """
        )

        return self.predict(prompt)


class ReflectionModule(dspy.Module):
    """Module for self-reflection and analysis of reasoning."""

    input_reasoning = InputField(desc="Previous reasoning or decision process")
    input_feedback = InputField(desc="Optional feedback or critique")

    insights = OutputField(desc="Key insights from reflection")
    improvements = OutputField(desc="Suggested improvements")

    def forward(self, reasoning: str, feedback: str | None = None) -> dspy.Prediction:
        """
        Generate reflective analysis of previous reasoning.

        Args:
            reasoning: The previous reasoning or decision process to reflect on
            feedback: Optional feedback or critique to consider

        Returns:
            A prediction containing insights and suggested improvements
        """
        prompt_text = f"""
        Previous Reasoning: {reasoning}
        """

        if feedback:
            prompt_text += f"\nFeedback: {feedback}"

        prompt = dspy.ChainOfThought(
            prompt_text
            + """

            Let's reflect on this reasoning:
            1) What are the key insights?
            2) What could be improved?
            3) How can we enhance the logic?

            Provide specific, actionable insights.
            """
        )

        return self.predict(prompt)
