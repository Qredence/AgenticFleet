"""Basic example of using AgenticFleet with Chainlit UI and AutoGen agents."""

import logging
import os

import chainlit as cl
from autogen_agentchat.messages import TextMessage
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize global variables
model_client: AzureOpenAIChatCompletionClient | None = None
agent_team = {}


@cl.on_chat_start
async def setup():
    """Initialize the chat session with necessary agents and configurations."""
    try:
        # Initialize Azure OpenAI client
        global model_client
        model_client = AzureOpenAIChatCompletionClient(
            model="gpt-4o-mini",
            deployment="gpt-4o-mini",
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            streaming=True,
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "family": "azure",
                "architecture": "gpt-4o-mini",
            },
        )

        # Initialize agents
        global agent_team
        agent_team = {
            "web_surfer": MultimodalWebSurfer(
                name="WebSurfer",
                model_client=model_client,
                description="Navigates and extracts information from the web",
                headless=True,
                start_page="https://www.bing.com",
                animate_actions=False,
            ),
            "file_surfer": FileSurfer(
                name="FileSurfer",
                model_client=model_client,
                description="Manages file operations and information extraction",
            ),
            "coder": MagenticOneCoderAgent(name="Coder", model_client=model_client),
            "executor": LocalCommandLineCodeExecutor(
                work_dir=os.path.join(os.getcwd(), "workspace"),
                timeout=300,  # 5 minutes
            ),
        }

        # Send welcome message
        await cl.Message(
            content="🚀 Welcome to AgenticFleet! I'm ready to help you with:",
            elements=[
                cl.Text(content="- Web searches and information gathering", display="inline"),
                cl.Text(content="- File operations and management", display="inline"),
                cl.Text(content="- Code generation and execution", display="inline"),
            ],
        ).send()

    except Exception as e:
        error_msg = f"Setup failed: {str(e)}"
        logger.error(error_msg)
        await cl.Message(content=f"⚠️ {error_msg}").send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming chat messages."""
    try:
        # Create task list to track progress
        task_list = cl.TaskList()
        await task_list.send()

        # Process message through each agent
        for agent_name, agent in agent_team.items():
            # Update task status
            task = cl.Task(title=f"Processing with {agent_name}", status=cl.TaskStatus.RUNNING)
            task_list.tasks.append(task)
            await task_list.update()

            try:
                # Convert message to TextMessage for agent processing
                agent_message = TextMessage(content=message.content, source="user")

                # Process message with agent
                if hasattr(agent, "process_message"):
                    response = await agent.process_message(agent_message)

                    # Handle response
                    if response:
                        await cl.Message(content=str(response), author=agent_name).send()

                # Update task status
                task.status = cl.TaskStatus.DONE
                await task_list.update()

            except Exception as e:
                logger.error(f"Error with {agent_name}: {str(e)}")
                task.status = cl.TaskStatus.FAILED
                await task_list.update()
                await cl.Message(
                    content=f"⚠️ Error with {agent_name}: {str(e)}", author="System"
                ).send()

    except Exception as e:
        error_msg = f"Message processing failed: {str(e)}"
        logger.error(error_msg)
        await cl.Message(content=f"⚠️ {error_msg}").send()


@cl.on_stop
async def cleanup():
    """Clean up resources when the chat session ends."""
    try:
        for agent in agent_team.values():
            if hasattr(agent, "cleanup"):
                await agent.cleanup()
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")


if __name__ == "__main__":
    cl.run()
