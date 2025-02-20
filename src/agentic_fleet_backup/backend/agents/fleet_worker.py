import logging

from autogen_agentchat.agents import CodeExecutorAgent

from agentic_fleet.backend.agents.base_model_agent import BaseModelAgent


class FleetWorker(BaseModelAgent, CodeExecutorAgent):
    """
    Custom FleetWorker agent that extends CodeExecutorAgent with additional functionality and custom logging,
    and now inherits from BaseModelAgent for consistent structure.
    """

    def __init__(self, name: str, code_executor: CodeExecutorAgent, description: str = "Executes and monitors code tasks with precision."):
        BaseModelAgent.__init__(self, name=name, description=description, role="Code Executor")
        CodeExecutorAgent.__init__(self, name=name, code_executor=code_executor) # Pass the code_executor
        self.custom_attr = "FleetWorker Custom Attribute"
        logging.info("FleetWorker initialized with custom attributes in agents folder.")

    async def execute(self, code):
        """
        Execute the given code, leveraging the base CodeExecutorAgent's capabilities.
        Logs usage of the custom attribute as an example of extending functionality.
        """
        logging.info(f"FleetWorker executing code with custom attribute: {self.custom_attr}")
        result = await super().execute_code(code)  # Provided by CodeExecutorAgent
        return result

    async def on_messages(self, messages, cancellation_token):
        """Handles incoming messages, delegating to CodeExecutorAgent."""
        return await CodeExecutorAgent.on_messages(self, messages, cancellation_token)

    async def on_reset(self, cancellation_token):
        """Resets the agent's state."""
        await CodeExecutorAgent.on_reset(self, cancellation_token)
        logging.info(f"[FleetWorker] Resetting {self.name}")
