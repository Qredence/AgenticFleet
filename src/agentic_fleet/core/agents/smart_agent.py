"""
Smart Agent Module.

This module provides a Smart Agent implementation that uses Azure OpenAI API
to generate responses and pulls data from a vector database.
"""

import base64
import inspect
import json
import os
from logging import Logger
from types import MappingProxyType
from typing import Any

import fsspec
import fsspec.implementations

try:
    from functions import SearchVectorFunction
except ImportError:
    SearchVectorFunction = Any  # Fallback for type hinting if functions module is not found
from autogen_agentchat.messages import ChatMessage  # Assuming ChatMessage is still here
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall

from agentic_fleet.core.agents.base import BaseAgent
from agentic_fleet.schemas.agent import Agent as SmartAgentModelConfiguration


class Smart_Agent(BaseAgent):
    """Smart agent that uses the pulls data from a vector database and uses the Azure OpenAI API to generate responses.

    This agent extends the base Agent class and provides functionality to interact with
    Azure OpenAI API and vector databases for enhanced reasoning capabilities.

    Attributes:
        smart_agent_config: Configuration specific to the SmartAgent.
        search_vector_function: Function to search vector database.
        # Conversation history is managed by BaseAgent/AutoGen.
        # Tool/function registration will need to be adapted to AutoGen's mechanisms.
    """

    def __init__(
        self,
        logger: Logger,
        agent_configuration: SmartAgentModelConfiguration,
        client: ChatCompletionClient,
        search_vector_function: SearchVectorFunction,
        init_history: list[dict],
        fs: fsspec.AbstractFileSystem,
        max_run_per_question: int = 10,
        max_question_to_keep: int = 3,
        max_question_with_detail_hist: int = 1,
        image_directory: str = "images",
        **kwargs: Any,
    ) -> None:
        """Initialize the Smart Agent.

        Args:
            logger: Logger instance for logging agent activities.
            agent_configuration: Configuration for the SmartAgent (must be Pydantic or converted).
            client: Model client for API interactions (compatible with BaseAgent).
            search_vector_function: Function to search vector database.
            init_history: Initial conversation history.
            fs: File system implementation for handling files.
            max_run_per_question: Maximum number of runs per question.
            max_question_to_keep: Maximum number of questions to keep in history.
            max_question_with_detail_hist: Maximum number of questions with detailed history.
            image_directory: Directory to store images.
        """
        # Initialize BaseAgent
        # We need to extract/define name, description, system_message for BaseAgent
        # agent_configuration should provide these or have defaults.
        base_agent_name = agent_configuration.name
        base_agent_description = agent_configuration.description
        # System message could come from agent_configuration or be a default.
        base_system_message = kwargs.pop("system_message", self._get_default_system_message())

        super().__init__(
            name=base_agent_name,
            model_client=client,
            description=base_agent_description,
            system_message=base_system_message,
            **kwargs,
        )

        self.smart_agent_config = agent_configuration  # Store the specific config
        self._logger = logger  # Can keep for specific logging, though BaseAgent has self.logger

        # self.__client is now self.model_client from BaseAgent
        self.__max_run_per_question: int = max_run_per_question
        self.__max_question_to_keep: int = max_question_to_keep
        self.__max_question_with_detail_hist: int = max_question_with_detail_hist

        # Tool/function registration needs to adapt to AutoGen.
        # For now, store the search function. We'll need to register it with AutoGen later.
        self.search_vector_function = search_vector_function
        # Example: self.register_function(SearchVectorFunction(...)) if SearchVectorFunction is adapted.

        # Conversation history (`init_history`, `self._conversation`) is now managed by AutoGen.
        # If init_history is critical, it needs to be passed when starting a chat.

        self.__fs: fsspec.AbstractFileSystem = fs
        self.__image_directory: str = image_directory

    async def process_message(self, message: str | ChatMessage, **kwargs) -> dict[str, Any]:
        """Run the agent with the given user input.

        Processes the user input, generates a response using the Azure OpenAI API,
        and handles any tool calls required.

        Args:
            message: The user's input text or ChatMessage.
            **kwargs: Additional arguments (e.g., history, context from AutoGen flow).

        Returns:
            Dict[str, Any]: The agent's response.
        """
        if isinstance(message, ChatMessage):
            user_input = message.content
        else:
            user_input = message

        if not user_input:
            # BaseAgent.process_message expects a dict.
            return {"content": "No input provided.", "role": "assistant"}

        # Conversation history will be managed by AutoGen and passed to generate_response.
        # For this refactoring, we'll simplify the direct history manipulation.
        # The complex loop and direct OpenAI calls need to be replaced.

        # This is a simplified flow. The original's tool use logic is complex and needs
        # full integration with AutoGen's tool calling.
        run_count = 0
        current_messages: list[ChatMessage] = []
        if "history" in kwargs and kwargs["history"]:
            current_messages.extend(kwargs["history"])
        current_messages.append(UserMessage(content=user_input, source="user"))

        while True:
            if run_count >= self.__max_run_per_question:
                self.logger.debug(
                    msg=f"Need to move on from this question due to max run count reached ({run_count} runs)"
                )
                final_content = "I am unable to answer this question at the moment, please ask another question."
                role = "assistant"
                break

            # Use BaseAgent's generate_response
            # Tool specs should be registered with the agent for AutoGen to handle.
            # For now, we assume tools are handled by AutoGen's flow if registered.
            llm_response = await super().generate_response(
                messages=current_messages,
                temperature=0.2,  # Or from self.smart_agent_config.model_temperature
                # AutoGen handles tool_choice based on registered functions/tools
            )

            run_count += 1
            response_message_content = llm_response.content if llm_response else ""

            # AutoGen's flow would typically handle tool calls.
            # If llm_response contains tool_calls, AutoGen would execute them and call agent again.
            # This simplified version assumes the response is final or tool calls are handled externally by AutoGen.
            # The original __verify_openai_tools logic needs to be re-evaluated in context of AutoGen tools.
            if (
                not llm_response or not llm_response.message.tool_calls
            ):  # Simplified: break if no tool calls
                final_content = response_message_content
                role = "assistant"
                current_messages.append(
                    SystemMessage(content=final_content, source="assistant")
                )  # Add assistant response to history for next turn
                break
            else:
                # Placeholder: In a full AutoGen integration, tool calls would be processed here
                # by the framework, leading to another agent turn.
                self.logger.info(f"LLM suggested tool calls: {llm_response.message.tool_calls}")
                # For this refactor, we'll assume the tool call is a reason to stop and let AutoGen handle it.
                # Or, if this agent is *meant* to execute its own tools in a loop, that's a deeper change.
                final_content = response_message_content  # Or a message about tool call
                role = "assistant"  # This might be a tool message in AutoGen
                current_messages.append(llm_response.message)  # Add the message with tool calls
                # Here, we'd typically return something that AutoGen understands as a tool request.
                # For simplicity in this step, we break.
                break

        return {
            "content": final_content,
            "role": role,
            "metadata": llm_response.model_dump() if llm_response else {},
        }

    def _check_args(self, function, args) -> bool:
        """Check if the arguments match the function signature.

        Args:
            function: The function to check arguments for.
            args: The arguments to check.

        Returns:
            bool: True if arguments match the function signature, False otherwise.
        """
        sig: inspect.Signature = inspect.signature(obj=function)
        params: MappingProxyType[str, inspect.Parameter] = sig.parameters

        for name in args:
            if name not in params:
                return False

        for name, param in params.items():
            if param.default is param.empty and name not in args:
                return False

        return True

    def _verify_openai_tools_results(self, tool_calls: list[ChatCompletionMessageToolCall]) -> None:
        """Verify that the tool calls from OpenAI are valid.

        Args:
            tool_calls: List of tool calls from OpenAI.

        Raises:
            ValueError: If a tool call is invalid.
        """
        for tool_call in tool_calls:
            function_name: str = tool_call.function.name
            self.logger.debug(msg=f"Recommended Function call: {function_name}")

            # verify function exists
            if function_name != "search":  # Placeholder for actual registered function name
                self.logger.debug(
                    msg=f"Function {function_name} does not exist or not handled, retrying"
                )
                break

            function_to_call = self.search_vector_function.search

            try:
                function_args = json.loads(s=tool_call.function.arguments)
            except json.JSONDecodeError as e:
                self.logger.error(msg=e)
                break

            if self._check_args(function=function_to_call, args=function_args) is False:
                break
            else:
                pass  # Placeholder - AutoGen should handle execution and adding tool response to history.

    def _generate_search_function_response(self, function_response):
        """Generate a response from the search function results.

        Args:
            function_response: The response from the search function.

        Returns:
            str: A formatted response based on the search results.
        """
        search_function_response = []

        for item in function_response:
            image_path = os.path.join(self.__image_directory, item["image_path"])
            related_content = item["related_content"]

            image_file: str | bytes = self.__fs.read_bytes(path=image_path)
            image_bytes: bytes | None = image_file if isinstance(image_file, bytes) else None
            image_bytes = (
                image_file.encode(encoding="utf-8") if isinstance(image_file, str) else image_file
            )
            base64_image: str = base64.b64encode(s=image_bytes).decode(encoding="utf-8")
            self._logger.debug("image_path: ", image_path)

            search_function_response.append({"type": "text", "text": f"file_name: {image_path}"})
            search_function_response.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )
            search_function_response.append(
                {
                    "type": "text",
                    "text": f"HINT: The following kind of content might be related to this topic\n: {related_content}",
                }
            )

        return search_function_response

    def _get_default_system_message(self) -> str:
        return "You are a smart AI assistant with vector search capabilities. Use your tools when appropriate."

    def _get_default_description(self) -> str:
        return "A smart agent that can perform vector searches and complex reasoning."

    def dump_component(self) -> dict[str, Any]:
        base_dump = super().dump_component()
        # Assuming self.smart_agent_config is Pydantic
        if hasattr(self.smart_agent_config, "model_dump"):
            base_dump["config"][
                "smart_agent_specific_config"
            ] = self.smart_agent_config.model_dump()
        elif isinstance(self.smart_agent_config, dict):  # If it's just a dict
            base_dump["config"]["smart_agent_specific_config"] = self.smart_agent_config
        # Add other serializable parts of SmartAgent's unique state if necessary
        return base_dump

    @classmethod
    def load_component(cls, config_dict: dict[str, Any]) -> "Smart_Agent":
        agent_config_data = config_dict.get("config", {})
        smart_agent_specific_config_data = agent_config_data.pop("smart_agent_specific_config", {})

        # Reconstruct SmartAgentModelConfiguration from smart_agent_specific_config_data
        # This assumes SmartAgentModelConfiguration can be initialized from a dict.
        # Ensure all required fields for schemas.agent.Agent are present or have defaults
        # Required fields for schemas.agent.Agent: id, name, description, model, created_at, updated_at
        # These might not all be in smart_agent_specific_config_data, this part is tricky for load_component
        # For now, let's assume smart_agent_specific_config_data has enough, or defaults are handled by Pydantic if optional.
        # This highlights a potential issue if not all fields for schemas.agent.Agent are persisted.
        # A simpler approach for specific config might be a less restrictive Pydantic model for SmartAgent *internal* state.

        # For the purpose of this refactor, let's assume smart_agent_specific_config_data
        # is the *complete* dictionary for SmartAgentModelConfiguration (schemas.agent.Agent)
        if not all(
            k in smart_agent_specific_config_data
            for k in ["id", "name", "description", "model", "created_at", "updated_at"]
        ):
            # This is a fallback if the config is partial, which is not ideal for a strict Pydantic model
            # A proper factory would handle this better by fetching full agent data if only ID is provided.
            temp_id = smart_agent_specific_config_data.get("id", "temp_smart_agent_id")
            temp_name = smart_agent_specific_config_data.get(
                "name", agent_config_data.get("name", "smart_agent")
            )
            temp_description = smart_agent_specific_config_data.get(
                "description", agent_config_data.get("description")
            )
            temp_model = smart_agent_specific_config_data.get(
                "model", "default_model"
            )  # model is required
            from datetime import datetime  # ensure datetime is imported

            now = datetime.now()
            rehydrated_smart_config = SmartAgentModelConfiguration(
                id=temp_id,
                name=temp_name,
                description=temp_description,
                model=temp_model,
                created_at=smart_agent_specific_config_data.get("created_at", now),
                updated_at=smart_agent_specific_config_data.get("updated_at", now),
                capabilities=smart_agent_specific_config_data.get("capabilities", []),
                parameters=smart_agent_specific_config_data.get("parameters", {}),
            )
        else:
            rehydrated_smart_config = SmartAgentModelConfiguration(
                **smart_agent_specific_config_data
            )

        # Other dependencies like logger, search_vector_function, fs need to be handled by the factory/registry
        # For now, we pass them as None or with placeholders.
        # This part highlights that `load_component` often needs a richer context or a factory.

        # Create a dummy logger for now, real one should be injected
        temp_logger = logging.getLogger(f"{cls.__name__}_temp")

        # Create a dummy search_vector_function, real one injected
        class DummySearchVectorFunction:
            def search(self, *args, **kwargs):
                return "Dummy search results"

        # Create dummy fs
        class DummyFs:
            pass

        return cls(
            name=agent_config_data.get("name", "smart_agent"),
            description=agent_config_data.get("description"),
            system_message=agent_config_data.get("system_message"),
            model_client=None,  # To be injected
            agent_configuration=rehydrated_smart_config,
            logger=temp_logger,
            search_vector_function=DummySearchVectorFunction(),
            fs=DummyFs(),
            init_history=[],  # History managed by AutoGen
            # Other params like max_run_per_question can come from rehydrated_smart_config or defaults
        )
