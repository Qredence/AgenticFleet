    # Standard library imports
    import json
    import logging
    import os
    import re
    import time
    import traceback
    from abc import ABC
    from functools import lru_cache
    from pathlib import Path
    from typing import Any, Dict, List, Optional, Tuple, Union

    # Third-party imports
    import chainlit as cl
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    # AutoGen imports
    from autogen_agentchat.base import TaskResult
    from autogen_agentchat.messages import (
        ChatMessage,
        MultiModalMessage,
        TextMessage,
    )
    from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
    from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
    from autogen_ext.teams.magentic_one import MagenticOne
    from chainlit import (
        Message,
        Step,
        Task,
        TaskList,
        TaskStatus,
        User,
        oauth_callback,
        on_chat_start,
        on_message,
        on_settings_update,
        on_stop,
        user_session,
    )
    from chainlit.chat_settings import ChatSettings
    from chainlit.input_widget import Select, Slider, Switch
    from dotenv import load_dotenv
    from openai import AsyncAzureOpenAI
    from pydantic import BaseModel, ConfigDict, Field
    from typing_extensions import Annotated

    # Local imports
    from agentic_fleet.apps.chainlit_ui.agent_registry.default_agents import (
        initialize_agent_team,
        initialize_default_agents,
    )
    from agentic_fleet.config import config_manager
    from agentic_fleet.core.application.manager import ApplicationConfig, ApplicationManager
    from agentic_fleet.core.application.models import Settings
    from agentic_fleet.message_processing import process_response

    # Initialize logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Load environment variables
    load_dotenv()

    # Initialize configuration manager
    try:
        config_manager.load_all()
        logger.info("Successfully loaded all configurations")

        # Validate environment
        if error := config_manager.validate_environment():
            raise ValueError(error)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise

    # Get environment settings
    env_config = config_manager.get_environment_settings()

    # Constants
    STREAM_DELAY = env_config.get("stream_delay", 0.03)
    PORT = int(os.getenv("CHAINLIT_PORT", os.getenv("PORT", "8000")))
    HOST = os.getenv("CHAINLIT_HOST", os.getenv("HOST", "localhost"))

    # Get default values
    defaults = config_manager.get_defaults()
    DEFAULT_MAX_ROUNDS = defaults.get("max_rounds", 10)
    DEFAULT_MAX_TIME = defaults.get("max_time", 300)
    DEFAULT_MAX_STALLS = defaults.get("max_stalls", 3)
    DEFAULT_START_PAGE = defaults.get("start_page", "https://www.bing.com")
    DEFAULT_TEMPERATURE = defaults.get("temperature", 0.7)
    DEFAULT_SYSTEM_PROMPT = defaults.get("system_prompt", "")

    app_manager: Optional[ApplicationManager] = None


    # Factory function for client creation
    def create_client(
        model_name: str,
        streaming: bool = True,
        vision: bool = False,
        connection_pool_size: int = 10,
        request_timeout: int = 30,
    ) -> AzureOpenAIChatCompletionClient:
        """Create and return an Azure OpenAI client with the specified configuration."""
        return AzureOpenAIChatCompletionClient(
            model=model_name,
            deployment=model_name,
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model_streaming=streaming,
            model_info={
                "vision": vision,
                "function_calling": True,
                "json_output": True,
                "family": "gpt-4o" if "gpt-4o" in model_name else "azure",
                "architecture": model_name,
            },
            streaming=streaming,
            connection_pool_size=connection_pool_size,
            request_timeout=request_timeout,
        )


    # Add connection pooling for Azure client
    client = create_client(
        model_name="gpt-4o-mini-2024-07-18",
        streaming=True,
        vision=True,
        connection_pool_size=10,
        request_timeout=30,
    )


    # Add caching for config loading
    @lru_cache(maxsize=1)
    def load_cached_config():
        return config_manager.load_all()


    @cl.set_chat_profiles
    async def chat_profiles():
        """Define enhanced chat profiles with metadata and icons."""
        return [
            cl.ChatProfile(
                name="Magentic Fleet Fast",
                markdown_description=(
                    "**Speed-Optimized Workflow**\n\n"
                    "- Model: GPT-4o Mini (128k context)\n"
                    "- Response Time: <2s average\n"
                    "- Best for: Simple queries & quick tasks"
                ),
                icon="/public/icons/rocket.svg",
                metadata={
                    "model": "gpt-4o-mini",
                    "max_tokens": 128000,
                    "temperature_range": [0.3, 0.7],
                },
            ),
            cl.ChatProfile(
                name="Magentic Fleet Max",
                markdown_description=(
                    "**Advanced Reasoning Suite**\n\n"
                    "- Model: O3 Mini (128k context)\n"
                    "- Multi-agent collaboration\n"
                    "- Complex problem solving"
                ),
                icon="/public/icons/microscope.svg",
                metadata={
                    "model": "o3-mini",
                    "max_tokens": 128000,
                    "temperature_range": [0.5, 1.2],
                },
            ),
        ]


    @cl.author_rename
    def rename_author(orig_author: str) -> str:
        """Friendly agent names with emoji indicators"""
        rename_map = {
            "MagenticOne": "🤖 Magentic Assistant",
            "Orchestrator": "🎼 Orchestrator",
            "WebSurfer": "🌐 Web Navigator",
            "FileSurfer": "📁 File Explorer",
            "Coder": "👨‍💻 Code Architect",
            "Executor": "⚡ Action Runner",
            "System": "🛠️ System",
            "Tool Manager": "🔧 Tool Manager",
            "Assistant": "🤖 Assistant",
            "user": "👤 User",
            "Chatbot": "💬 Assistant",
        }
        # If the author is already prefixed with an emoji, return as is
        if orig_author and any(ord(c) > 0x1F00 for c in orig_author):
            return orig_author
        return rename_map.get(orig_author, f"🔹 {orig_author}")


    @cl.action_callback("reset_agents")
    async def on_reset(action: cl.Action):
        """Reset agent team with confirmation"""
        global app_manager
        if app_manager:
            await app_manager.shutdown()
        await on_chat_start()
        await cl.Message(content="🔄 Agents successfully reset!", author="System").send()


    async def ask_user_for_input(question: str, options: List[str] = None) -> str:
        """Ask the user for input with optional choices.

        Args:
            question: The question to ask the user
            options: Optional list of choices for the user to select from

        Returns:
            The user's response as a string
        """
        if options:
            # Use AskActionMessage for multiple-choice questions
            res = await cl.AskActionMessage(
                content=question, actions=[{"name": opt, "value": opt} for opt in options]
            ).send()
            return res["value"]
        else:
            # Use AskUserMessage for free-form input
            res = await cl.AskUserMessage(content=question).send()
            return res["content"]


    def detect_and_render_data(content: Any) -> Tuple[str, List[Any]]:
        """Detect and render data visualizations from content.

        Args:
            content: The content to analyze and render

        Returns:
            Tuple of (text_content, elements) where elements are Chainlit UI elements
        """
        elements = []
        text_content = ""

        # Handle None case
        if content is None:
            return "", elements

        # Handle list case - convert to string
        if isinstance(content, list):
            # If it's a list of simple types, join them
            if all(isinstance(item, (str, int, float, bool)) for item in content):
                text_content = "\n".join(str(item) for item in content)
            else:
                # For complex lists, try to convert to DataFrame if possible
                try:
                    df = pd.DataFrame(content)
                    elements.append(cl.DataFrame(data=df, name="list_data_view"))
                    text_content = "List data (see below)"
                except:
                    # Fall back to string representation
                    text_content = str(content)
            return text_content, elements

        # Handle pandas DataFrame
        if isinstance(content, pd.DataFrame):
            elements.append(cl.DataFrame(data=content, name="data_view"))
            text_content = "DataFrame generated (see below)"

        # Handle matplotlib/seaborn figure
        elif isinstance(content, plt.Figure):
            elements.append(cl.Image(content, name="plot_view"))
            text_content = "Plot generated (see below)"

        # Handle numpy arrays
        elif isinstance(content, np.ndarray):
            if content.ndim <= 2:  # Convert 1D or 2D arrays to DataFrame
                df = pd.DataFrame(content)
                elements.append(cl.DataFrame(data=df, name="array_view"))
                text_content = "Array data (see below)"
            else:
                text_content = str(content)

        # Handle dictionaries that might contain data
        elif isinstance(content, dict) and any(
            key in content for key in ["data", "values", "columns", "rows"]
        ):
            try:
                df = pd.DataFrame(content)
                elements.append(cl.DataFrame(data=df, name="dict_data_view"))
                text_content = "Data from dictionary (see below)"
            except:
                text_content = str(content)

        # Default case - return as string
        else:
            text_content = str(content) if content is not None else ""

        return text_content, elements


    def is_code_block(text: str) -> bool:
        """Check if text is primarily a code block.

        Args:
            text: Text to check

        Returns:
            True if text appears to be code, False otherwise
        """
        # Check for code block markers
        if re.search(r"```\w*\n.*?\n```", text, re.DOTALL):
            return True

        # Check for common code patterns
        code_patterns = [
            r"^(import|from)\s+\w+",  # Python imports
            r"^(def|class)\s+\w+",  # Python functions/classes
            r"^(function|const|let|var)\s+\w+",  # JavaScript
            r"^(public|private|class)\s+\w+",  # Java/C#
            r"<\w+[^>]*>.*?</\w+>",  # HTML/XML
        ]

        for pattern in code_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True

        return False


    def format_message_content(content: Any) -> str:
        """Format message content with proper markdown and structure.

        Args:
            content: The content to format

        Returns:
            Formatted content string
        """
        # Handle non-string inputs
        if content is None:
            return ""

        # Convert lists to strings
        if isinstance(content, list):
            # Join list items with newlines
            content = "\n".join(str(item) for item in content)
        elif not isinstance(content, str):
            # Convert any other non-string type to string
            content = str(content)

        # Now we can safely process the string
        if not content:
            return ""

        # Remove excessive newlines
        content = re.sub(r"\n{3,}", "\n\n", content.strip())

        # Process code blocks more safely
        # First, find all code blocks with their positions
        code_block_pattern = r"```(\w*)\n(.*?)\n```"
        code_blocks = []

        for match in re.finditer(code_block_pattern, content, re.DOTALL):
            full_match = match.group(0)
            lang = match.group(1) or ""
            code = match.group(2)
            start_pos = match.start()
            end_pos = match.end()

            # Only process non-code blocks (markdown/text) or blocks with no language
            if not lang or lang.lower() in ["markdown", "text", "md"]:
                if not is_code_block(code):
                    # Replace this block with just the code content
                    code_blocks.append((start_pos, end_pos, full_match, code.strip()))

        # Replace blocks from end to start to avoid position shifts
        for start_pos, end_pos, full_match, replacement in sorted(
            code_blocks, reverse=True
        ):
            content = content[:start_pos] + replacement + content[end_pos:]

        # Add bullet points to lists
        content = re.sub(r"^(\d+\.\s)", "• ", content, flags=re.MULTILINE)

        return content


    # Setup chat settings function
    async def setup_chat_settings():
        """Initialize chat settings with default values."""
        settings = {
            "max_rounds": DEFAULT_MAX_ROUNDS,
            "max_time": DEFAULT_MAX_TIME,
            "max_stalls": DEFAULT_MAX_STALLS,
            "start_page": DEFAULT_START_PAGE,
            "temperature": DEFAULT_TEMPERATURE,
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
        }
        cl.user_session.set("settings", settings)

        # Register chat settings
        await cl.ChatSettings(
            [
                Select(
                    id="model",
                    label="Model",
                    values=["gpt-4o-mini", "o3-mini"],
                    initial_value="gpt-4o-mini",
                ),
                Slider(
                    id="temperature",
                    label="Temperature",
                    initial=DEFAULT_TEMPERATURE,
                    min=0.0,
                    max=1.0,
                    step=0.1,
                ),
                Slider(
                    id="max_rounds",
                    label="Max Rounds",
                    initial=DEFAULT_MAX_ROUNDS,
                    min=1,
                    max=20,
                    step=1,
                ),
            ]
        ).send()

        await cl.Message(
            content="⚙️ Chat settings initialized successfully", author="🛠️ System"
        ).send()


    @cl.on_settings_update
    async def update_settings(new_settings: Dict[str, Any]):
        """Update chat settings with new values."""
        current_settings = cl.user_session.get("settings", {})
        current_settings.update(new_settings)
        cl.user_session.set("settings", current_settings)
        await cl.Message(
            content="⚙️ Settings updated successfully", author="🛠️ System"
        ).send()


    @cl.on_chat_start
    async def on_chat_start():
        """Handle new chat session initialization."""
        app_user = cl.user_session.get("user")

        if app_user is None:
            # Use a default identifier for unauthenticated users
            identifier = "Guest"
        else:
            # Safely access the identifier with a fallback
            identifier = getattr(app_user, "identifier", "Guest")

        try:
            # Get the selected profile or create default
            profile = cl.user_session.get("chat_profile")

            # Create default profile if none selected or if profile is just a string
            if not profile or isinstance(profile, str):
                profile = cl.ChatProfile(
                    name="Magentic Fleet Fast",
                    markdown_description=(
                        "**Speed-Optimized Workflow**\n\n"
                        "- Model: GPT-4o Mini (128k context)\n"
                        "- Response Time: <2s average\n"
                        "- Best for: Simple queries & quick tasks"
                    ),
                    icon="/public/avatars/rocket.svg",
                    metadata={
                        "model": "gpt-4o-mini-2024-07-18",
                        "max_tokens": 128000,
                        "temperature_range": [0.3, 0.7],
                    },
                )
                logger.info("Using default profile")
                cl.user_session.set("chat_profile", profile)

            # Configure model based on profile name
            model_name = (
                "gpt-4o-mini-2024-07-18"
                if isinstance(profile, cl.ChatProfile) and "Fast" in profile.name
                else "o3-mini"
            )

            # Initialize Azure OpenAI client with appropriate configuration using factory
            client = create_client(
                model_name=model_name,
                streaming=True,
                vision=False,
            )

            # Initialize MagenticOne with configured client
            magentic_one = MagenticOne(
                client=client, hil_mode=True, code_executor=LocalCommandLineCodeExecutor()
            )

            # Store MagenticOne instance and profile in user session
            cl.user_session.set("magentic_one", magentic_one)
            cl.user_session.set("active_profile", profile)

            # Initialize application manager
            global app_manager
            app_manager = ApplicationManager(
                ApplicationConfig(
                    project_root=Path(__file__).parent.parent,
                    debug=env_config.get("debug", False),
                    log_level=env_config.get("log_level", "INFO"),
                )
            )
            await app_manager.start()

            # Initialize default agents
            default_agents = initialize_default_agents(
                app_manager, config_manager, cl.user_session, defaults, env_config
            )

            # Get team configuration
            team_config = config_manager.get_team_settings("magentic_fleet_one")

            # Add environment validation before initialization
            required_env_vars = [
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_API_VERSION",
            ]
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                raise ValueError(
                    f"Missing required environment variables: {', '.join(missing_vars)}"
                )

            # Initialize agent team
            agent_team = await initialize_agent_team(
                app_manager, cl.user_session, team_config, default_agents, defaults
            )

            # Add team validation
            if not agent_team or not hasattr(agent_team, "run_stream"):
                raise RuntimeError("Agent team initialization failed - invalid team object")
            cl.user_session.set("agent_team", agent_team)

            # Store settings in user session
            settings = {
                "max_rounds": DEFAULT_MAX_ROUNDS,
                "max_time": DEFAULT_MAX_TIME,
                "max_stalls": DEFAULT_MAX_STALLS,
                "start_page": DEFAULT_START_PAGE,
                "temperature": DEFAULT_TEMPERATURE,
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
            }
            cl.user_session.set("settings", settings)

            # Welcome message with profile details and reset control
            profile_name = (
                profile.name if isinstance(profile, cl.ChatProfile) else "Default Profile"
            )
            profile_desc = (
                profile.markdown_description
                if isinstance(profile, cl.ChatProfile)
                else "Standard configuration"
            )

            welcome_message = (
                f"🚀 Welcome to MagenticFleet!\n\n"
                f"**Active Profile**: {profile_name}\n"
                f"**Model**: {model_name}\n"
                f"**Temperature**: {DEFAULT_TEMPERATURE}\n"
                f"**Context Length**: 128,000 tokens\n\n"
                f"{profile_desc}"
            )

            await cl.Message(
                content=welcome_message,
                actions=[
                    cl.Action(
                        name="reset_agents",
                        label="🔄 Reset Agents",
                        tooltip="Restart the agent team",
                        payload={"action": "reset"},
                    )
                ],
            ).send()

            # Setup chat settings
            await setup_chat_settings()

        except Exception as e:
            error_msg = f"⚠️ Initialization failed: {str(e)}"
            logger.error(f"Chat start error: {traceback.format_exc()}")
            await cl.Message(content=error_msg).send()


    @cl.on_message
    async def on_message(message: cl.Message):
        """Process incoming messages with task tracking."""
        # Create an enhanced TaskList with icons
        task_list = cl.TaskList(
            title="🔄 Processing Request",
            status="Analyzing your query...",
        )
        await task_list.send()

        # Store the task list in user session for later updates
        cl.user_session.set("current_task_list", task_list)

        # Initialize plan steps tracking
        cl.user_session.set("plan_steps", {})
        cl.user_session.set("plan_tasks", {})

        try:
            # Check for reset command without showing a message
            # Handle both string and list content types
            if (
                isinstance(message.content, str)
                and message.content.strip().lower() == "/reset"
            ):
                await on_reset(cl.Action(name="reset_agents", payload={"action": "reset"}))
                task_list.status = "✅ Agents reset successfully"
                await task_list.send()
                return

            # Initialize agent team if needed
            team = cl.user_session.get("magentic_one")
            if not team:
                # Get settings from user session
                settings = cl.user_session.get("settings", {})
                team = MagenticOne(
                    name="AgenticFleet Team",
                    client=client,
                    code_executor=LocalCommandLineCodeExecutor(),
                )
                cl.user_session.set("magentic_one", team)

            # Update task list with processing task
            process_task = cl.Task(
                title="🧠 Processing with Agent Team",
                status=cl.TaskStatus.RUNNING,
                icon="🔄",
            )
            await task_list.add_task(process_task)

            # Create a list to collect responses
            collected_responses = []

            # Process with MagenticOne's run_stream
            async with cl.Step(name="Agent Processing", show_input=True) as step:
                step.input = message.content

                # Stream responses from MagenticOne
                # Ensure task is a string
                task_content = (
                    message.content
                    if isinstance(message.content, str)
                    else str(message.content)
                )
                async for event in team.run_stream(task=task_content):
                    # Process each event from the stream
                    if hasattr(event, "content"):
                        # Extract agent name and properly format it
                        agent_name = getattr(
                            event,
                            "author",
                            getattr(event, "name", getattr(event, "agent_type", "Agent")),
                        )

                        # Apply emoji and formatting to agent name
                        formatted_author = rename_author(agent_name)

                        # Check if content contains a question for the user
                        content = event.content
                        # Ensure content is a string
                        if not isinstance(content, str):
                            if content is None:
                                content = ""
                            elif isinstance(content, list):
                                content = "\n".join(str(item) for item in content)
                            else:
                                content = str(content)

                        # Check if this is the Orchestrator providing a plan
                        if agent_name == "Orchestrator" and "Here is the plan to follow as best as possible:" in content:
                            # Update the task list immediately
                            plan_task = cl.Task(
                                title="📋 Plan Created", 
                                status=cl.TaskStatus.RUNNING,
                                icon="📝"
                            )
                            await task_list.add_task(plan_task)
                            task_list.status = "🔄 Executing plan..."
                            await task_list.send()

                            # Extract the plan from the content
                            plan_text = content.split("Here is the plan to follow as best as possible:")[1].strip()

                            # Create task status tracking
                            task_status = {
                                "planning": cl.Text(name="planned_tasks", content="", display="side"),
                                "overview": cl.Text(name="task_overview", content="", display="side"),
                                "completion": cl.Text(name="completed_tasks", content="", display="side"),
                                "execution": cl.Text(name="execution_progress", content="", display="side")
                            }

                            # Extract and add individual plan steps as tasks
                            await extract_and_add_plan_tasks(plan_text, task_list, task_status, message.id)

                        # Check for plan updates from Orchestrator
                        elif agent_name == "Orchestrator" and any(marker in content for marker in [
                            "Updated plan:", 
                            "Next steps:", 
                            "Additional steps:",
                            "Revised plan:"
                        ]):
                            # Extract the updated plan
                            for marker in ["Updated plan:", "Next steps:", "Additional steps:", "Revised plan:"]:
                                if marker in content:
                                    plan_update = content.split(marker)[1].strip()
                                    task_status = {
                                        "planning": cl.Text(name="planned_tasks", content="", display="side"),
                                        "overview": cl.Text(name="task_overview", content="", display="side"),
                                        "completion": cl.Text(name="completed_tasks", content="", display="side"),
                                        "execution": cl.Text(name="execution_progress", content="", display="side")
                                    }
                                    await extract_and_add_plan_tasks(plan_update, task_list, task_status, message.id, is_update=True)
                                    break

                        if "?" in content and any(
                            phrase in content.lower()
                            for phrase in [
                                "what would you like",
                                "do you want",
                                "should i",
                                "would you prefer",
                                "can you clarify",
                            ]
                        ):
                            # This might be a question for the user
                            if (
                                "options:" in content.lower()
                                or "options are:" in content.lower()
                            ):
                                # Try to extract options
                                options_text = content.split("options:", 1)[-1].split(
                                    "options are:", 1
                                )[-1]
                                options = [
                                    opt.strip().strip("*-•").strip()
                                    for opt in re.split(r"[\n*•-]", options_text)
                                    if opt.strip()
                                ]

                                # Ask the user and wait for response
                                user_response = await ask_user_for_input(
                                    content, options if options else None
                                )

                                # Send the user's response back to the agent
                                await cl.Message(
                                    content=user_response, author="👤 User"
                                ).send()
                                collected_responses.append(
                                    f"User response: {user_response}"
                                )
                                continue

                            # If we can't extract options but it seems like a question
                            if re.search(r"\?\s*$", content.split("\n")[-1]):
                                user_response = await ask_user_for_input(content)
                                await cl.Message(
                                    content=user_response, author="👤 User"
                                ).send()
                                collected_responses.append(
                                    f"User response: {user_response}"
                                )
                                continue

                        # Check for data visualizations
                        if hasattr(event, "data") and event.data:
                            text, elements = detect_and_render_data(event.data)
                            if elements:
                                await cl.Message(
                                    content=content,
                                    author=formatted_author,
                                    elements=elements,
                                ).send()
                                collected_responses.append(content)
                                continue

                        # Format the content
                        formatted_content = format_message_content(content)

                        # Determine if this is code and set language accordingly
                        language = "markdown"
                        if is_code_block(content):
                            language = "python"  # Default to Python, could be improved to detect language

                        # Send the message
                        await cl.Message(
                            content=formatted_content,
                            author=formatted_author,
                            language=language,
                        ).send()
                        collected_responses.append(content)

            # Mark processing task as complete
            process_task.status = cl.TaskStatus.DONE
            task_list.status = "✅ Processing complete"
            await task_list.send()

        except Exception as e:
            error_task = cl.Task(
                title="❌ Error Processing", status=cl.TaskStatus.FAILED, icon="⚠️"
            )
            await task_list.add_task(error_task)
            task_list.status = f"⚠️ Error: {str(e)}"
            await task_list.send()

            await cl.Message(
                content=f"Error: {str(e)}", author="🛠️ System", language="text"
            ).send()
            logger.error(f"Message processing error: {traceback.format_exc()}")


    async def extract_and_add_plan_tasks(
        plan_text: str, 
        task_list: cl.TaskList, 
        task_status: Dict[str, cl.Text], 
        message_id: str,
        is_update: bool = False
    ):
        """Extract plan steps and add them as individual tasks to the TaskList.

        Args:
            plan_text: The plan text to extract steps from
            task_list: The TaskList to add tasks to
            task_status: Dictionary of Text elements for status updates
            message_id: ID of the message to associate status updates with
            is_update: Whether this is an update to an existing plan
        """
        # Extract tasks using regex patterns
        tasks = []

        # Look for numbered steps (e.g., "1. Do something")
        for task in re.finditer(r"\d+\.\s+(.+?)(?=\n\d+\.|\n\n|$)", plan_text):
            tasks.append(task.group(1).strip())

        # If no numbered steps found, try looking for bullet points
        if not tasks:
            for task in re.finditer(r"[-*•]\s+(.+?)(?=\n[-*•]|\n\n|$)", plan_text):
                tasks.append(task.group(1).strip())
        
        # If still no tasks found, split by newlines and filter out empty lines
        if not tasks:
            tasks = [line.strip() for line in plan_text.split("\n") if line.strip()]

        if tasks:
            timestamp = time.strftime("%H:%M:%S")

            # Get existing plan steps or initialize empty dict
            plan_steps = cl.user_session.get("plan_steps", {})
            plan_tasks = cl.user_session.get("plan_tasks", {})

            # Update planning section
            planning_element = cl.Text(
                name="planned_tasks",
                content=task_status["planning"].content
                + f"\n[{timestamp}] 📋 {'Updated' if is_update else 'Initial'} Task Breakdown:\n"
                + "\n".join(f"{i}. {task.strip()}" for i, task in enumerate(tasks, 1))
                + "\n",
                display="side",
            )
            await planning_element.send(for_id=message_id)
            task_status["planning"] = planning_element

            # Update overview
            overview_element = cl.Text(
                name="task_overview",
                content=task_status["overview"].content
                + f"\n[{timestamp}] 📝 {'Updated plan with' if is_update else 'Identified'} {len(tasks)} tasks to execute\n",
                display="side",
            )
            await overview_element.send(for_id=message_id)
            task_status["overview"] = overview_element

            # Add each task to the TaskList
            for i, task_text in enumerate(tasks):
                task_id = f"plan_task_{len(plan_steps) + i + 1}"

                # Create a new task in the TaskList
                plan_task_item = cl.Task(
                    title=f"Step {len(plan_steps) + i + 1}: {task_text[:50]}{'...' if len(task_text) > 50 else ''}",
                    status=cl.TaskStatus.READY,
                    icon="📌"
                )
                await task_list.add_task(plan_task_item)

                # Store the task in the session for later reference
                plan_tasks[task_id] = plan_task_item
                plan_steps[task_id] = task_text

    # Update the session with the new tasks
    cl.user_session.set("plan_steps", plan_steps)
    cl.user_session.set("plan_tasks", plan_tasks)
