# Standard library imports
import logging
import os
import traceback
import uuid
from pathlib import Path

# Third-party imports
import chainlit as cl
from chainlit import on_chat_start, on_message, on_settings_update, on_stop
from dotenv import load_dotenv

# Local imports - using the modular components
from agentic_fleet.config import config_manager

# Agent and Team specific imports
from agentic_fleet.core.agents.coding_agent import CodingAgent, CodingConfig
from agentic_fleet.core.agents.smart_agent import Smart_Agent
from agentic_fleet.core.agents.team_factory import TeamFactory
from agentic_fleet.core.agents.web_search_agent import WebSearchAgent, WebSearchConfig
from agentic_fleet.core.application.manager import ApplicationConfig, ApplicationManager
from agentic_fleet.schemas.agent import Agent as SmartAgentModelConfiguration
from agentic_fleet.services.chat_service import ChatService
from agentic_fleet.services.client_factory import get_cached_client
from agentic_fleet.ui.message_handler import handle_chat_message, on_reset
from agentic_fleet.ui.settings_handler import SettingsManager

# Azure AI imports - switched to Gemini
# from autogen_ext.models.azure import AzureAIChatCompletionClient  # Commented out

# For using the original Azure OpenAI client - commented out
# from autogen_core.models import UserMessage
# from autogen_ext.models.openai import OpenAIChatCompletionClient  # Using OpenAI interface for Gemini

# Google Gemini imports - Direct approach
# import google.generativeai as genai
# from autogen_ext.models.base import ModelClient, ModelOutput



# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(Path(__file__).parent.parent.parent, ".env"))
logger.info(
    f"Environment variables loaded. AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}"
)

# Initialize application manager
app_manager: ApplicationManager | None = None

# Initialize settings manager
settings_manager = SettingsManager()

# Initialize client
client = None

# Initialize chat service
chat_service = ChatService()


# Hook into chainlit events
@on_chat_start
async def start_chat(profile: cl.ChatProfile | None = None):
    """Initialize the chat session with the selected profile."""
    global client, app_manager

    try:
        # Initialize configuration
        config_manager.load_all()
        logger.info("Successfully loaded all configurations")

        # Validate environment - Check for API keys
        # For demo purposes, we're using a mock client
        gemini_api_key = os.getenv("GEMINI_API_KEY", "mock-key")

        # Run any additional environment validation
        if error := config_manager.validate_environment():
            raise ValueError(error)

        # Get environment settings
        env_config = config_manager.get_environment_settings()

        # Use Azure OpenAI model (real LLM client)
        model_name = os.getenv(
            "AZURE_OPENAI_MODEL", "gpt-4.1-nano"
        )  # Default to gpt-4.1-nano if not set

        try:
            # Create a real LLM client using get_cached_client
            client = get_cached_client(model_name)
            # Set the model name for UI display
            client.model_info = {"name": model_name}
            logger.info(f"Successfully initialized real LLM client for: {model_name}")
        except Exception as e_client:
            logger.error(f"Error initializing real LLM client: {e_client}", exc_info=True)
            await cl.Message(content=f"⚠️ Error initializing LLM client: {str(e_client)}").send()
            return

        # Initialize application manager
        app_manager = ApplicationManager(
            ApplicationConfig(
                project_root=Path(__file__).parent.parent,
                debug=getattr(env_config, "debug", False),
                log_level=getattr(env_config, "log_level", "INFO"),
            )
        )
        await app_manager.start()

        # Initialize task list
        from agentic_fleet.ui.task_manager import initialize_task_list

        await initialize_task_list()

        # Get Azure OpenAI configuration from environment
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")

        # Instantiate available agents, passing the client
        available_agents_pool = {}

        try:
            logger.info("Instantiating Coder agent...")
            coding_config = CodingConfig()  # Using default config for now
            coder = CodingAgent(name="coder", model_client=client, config=coding_config)
            available_agents_pool["coder"] = coder
            logger.info("Coder agent instantiated.")

            logger.info("Instantiating WebSearchAgent agent...")
            web_search_config = WebSearchConfig()  # Using default config
            web_surfer = WebSearchAgent(
                name="web_surfer", model_client=client, config=web_search_config
            )
            available_agents_pool["web_surfer"] = web_surfer
            logger.info("WebSearchAgent agent instantiated.")

            logger.info("Instantiating Smart_Agent...")
            # Basic SmartAgentModelConfiguration - this will likely need more fields from its Pydantic definition
            # Fields like model_name, endpoint might be needed by the schema, even if BaseAgent uses client.
            smart_agent_config = SmartAgentModelConfiguration(
                name="smart_agent_basic",
                description="A basic Smart Agent instance.",
                model_name="gpt-4.1-nano",  # Placeholder, BaseAgent uses the client's model
                endpoint="placeholder_endpoint",  # Placeholder
                # Add other required fields from agentic_fleet.schemas.agent.Agent if they cause validation errors
            )
            # Mock/dummy dependencies for SmartAgent
            import logging as py_logging  # To avoid conflict with chainlit logger

            import fsspec.implementations.memory
            from functions import SearchVectorFunction  # Assuming this is importable

            dummy_logger = py_logging.getLogger("SmartAgentLogger")

            # This SearchVectorFunction will need a proper implementation or a more robust mock
            class DummySearchVectorFunction(SearchVectorFunction):
                def __init__(self):
                    super().__init__(None, None, None, None, None)  # Dummy init

                def search(self, query: str, top_k: int = 5):
                    return []  # Dummy search

            dummy_search_func = DummySearchVectorFunction()
            dummy_fs = fsspec.implementations.memory.MemoryFileSystem()

            smart_agent = Smart_Agent(
                logger=dummy_logger,
                agent_configuration=smart_agent_config,
                client=client,  # This is the main model client from app.py
                search_vector_function=dummy_search_func,
                init_history=[],
                fs=dummy_fs,
            )
            available_agents_pool["smart_agent"] = smart_agent
            logger.info("Smart_Agent instantiated (with dummy dependencies).")

            # TODO: Instantiate other agents like file_surfer, executor, smart_agent as needed
            # For Smart_Agent, ensure its dependencies (SearchVectorFunction, fs, specific config) are met.

        except Exception as e:
            logger.error(f"Error instantiating base agents: {e}", exc_info=True)
            await cl.Message(content=f"⚠️ Error setting up base agents: {str(e)}").send()
            return

        # Initialize TeamFactory
        logger.info("Initializing TeamFactory...")
        team_factory = TeamFactory(model_client=client)
        logger.info("TeamFactory initialized.")

        # Create a custom team or use a specialization
        # For this test, let's create a custom team with coder and web_surfer
        try:
            logger.info("Creating custom agent team...")
            agent_team_manager = team_factory.create_custom_team(
                name="custom_coder_web_team",
                description="A team with a coder and a web surfer.",
                agents={"coder": coder, "web_surfer": web_surfer, "smart_agent": smart_agent},
                # OrchestratorConfig and team_config can be None to use defaults in TeamManager/TeamFactory
            )
            cl.user_session.set("agent_team_manager", agent_team_manager)
            logger.info(f"Successfully created team: {agent_team_manager.config.name}")
        except Exception as e:
            logger.error(f"Failed to create agent team: {e}", exc_info=True)
            await cl.Message(content=f"⚠️ Error creating agent team: {str(e)}").send()
            return

        # Set up default settings
        default_settings = settings_manager.get_default_settings()
        cl.user_session.set("settings", default_settings)

        # Set session ID for chat history
        session_id = str(uuid.uuid4())
        cl.user_session.set("session_id", session_id)

        # Setup chat settings UI
        await settings_manager.setup_chat_settings()

        # Get profile information for welcome message
        profile_name = profile.name if isinstance(profile, cl.ChatProfile) else "Default Profile"
        profile_desc = (
            profile.markdown_description
            if isinstance(profile, cl.ChatProfile)
            else "Standard configuration"
        )

        # Send welcome message
        welcome_message = (
            f"🚀 Welcome to MagenticFleet!\n\n"
            f"**Active Profile**: {profile_name}\n"
            f"**Team Active**: {agent_team_manager.config.name if cl.user_session.get('agent_team_manager') else 'MagenticOne (Legacy)'}\n"
            f"**LLM Model**: {model_name} (Azure OpenAI)\n"
            f"**Temperature**: {default_settings['temperature']}\n"
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
                ),
                cl.Action(
                    name="view_history",
                    label="📜 View Chat History",
                    tooltip="View previous conversations",
                    payload={"action": "history"},
                ),
            ],
        ).send()

    except Exception as e:
        error_msg = f"⚠️ Initialization failed: {str(e)}"
        logger.error(f"Chat start error: {traceback.format_exc()}")
        await cl.Message(content=error_msg).send()


@on_message
async def message_handler(message: cl.Message):
    """Handle incoming chat messages."""
    # Retrieve the correct team/agent manager from session
    agent_team_manager = cl.user_session.get("agent_team_manager")

    if agent_team_manager:
        await handle_chat_message(message, agent_team_manager)  # Pass our new manager
    else:
        # If agent_team_manager is not found, handle_chat_message will use its internal
        # logic to get the legacy_team or error out if no team is found.
        logger.info(
            "agent_team_manager not found, attempting to use legacy team via handle_chat_message."
        )
        await handle_chat_message(message)  # Call without agent_team_manager


@on_settings_update
async def handle_settings_update(settings: cl.ChatSettings):
    """Handle updates to chat settings."""
    await settings_manager.handle_settings_update(settings)


@cl.action_callback("reset_agents")
async def on_action_reset(action: cl.Action):
    """Handle reset action."""
    await on_reset(action)


@cl.action_callback("view_history")
async def on_action_view_history(action: cl.Action):
    """Handle view history action."""
    try:
        # Get the current session ID
        session_id = cl.user_session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            cl.user_session.set("session_id", session_id)

        # Get chat history for the current session
        messages = await chat_service.get_chat_history(session_id)

        if not messages:
            await cl.Message(content="No chat history found for this session.").send()
            return

        # Format the chat history
        history_content = "## 📜 Chat History\n\n"
        for i, msg in enumerate(messages, 1):
            sender = msg.sender if hasattr(msg, "sender") else "Unknown"
            content = msg.content if hasattr(msg, "content") else "No content"
            timestamp = (
                msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(msg, "timestamp") and msg.timestamp
                else "Unknown time"
            )

            history_content += f"### Message {i} - {sender} ({timestamp})\n\n"
            history_content += f"{content}\n\n"
            history_content += "---\n\n"

        # Display the chat history
        await cl.Message(content=history_content).send()

    except Exception as e:
        logger.error(f"Error displaying chat history: {str(e)}")
        await cl.Message(content=f"Error displaying chat history: {str(e)}").send()


@on_stop
async def on_chat_stop():
    """Clean up resources when the chat is stopped."""
    global app_manager

    if app_manager:
        try:
            await app_manager.shutdown()
            logger.info("Application manager stopped")
        except Exception as e:
            logger.error(f"Error shutting down application manager: {e}")

    # Clear user session
    session_vars = [
        "agent_team",
        "team",
        "app_manager",
        "settings",
        "ui_render_mode",
        "mcp_servers",
        "session_id",
    ]
    for key in session_vars:
        cl.user_session.set(key, None)


if __name__ == "__main__":
    import agentic_fleet.chainlit_app

    agentic_fleet.chainlit_app.main()
