"""
Chainlit application entry point for AgenticFleet.

This module serves as the primary entry point for the Chainlit UI application,
implementing best practices for message handling, error management, and step tracking.
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeAlias

import chainlit as cl
from dotenv import load_dotenv

# Type aliases
Message: TypeAlias = Any  # Replace with actual message type if available
TextMessage: TypeAlias = dict[str, Any]  # Define TextMessage type
ElementType: TypeAlias = Any  # Define ElementType for UI elements
ChatHistory: TypeAlias = list[dict[str, str]]  # Define chat history type

# Re-export for backward compatibility
__all__ = ["Message", "TextMessage", "ElementType", "ChatHistory"]

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agentic_fleet.log"),
    ],
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL = "gpt-4.1-nano"
MAX_MESSAGE_LENGTH = 4000  # Maximum characters before truncation

# Chainlit widgets
try:
    from chainlit.input_widget import Slider, TextInput
except ImportError:
    # For older versions of chainlit, fallback to chainlit.widgets
    try:
        from chainlit.widgets import Slider, TextInput
    except ImportError:
        Slider = TextInput = None

# === Default chat settings ===
DEFAULT_MAX_ROUNDS = 8
DEFAULT_MAX_TIME = 10
DEFAULT_MAX_STALLS = 3
DEFAULT_START_PAGE = "https://www.google.com"

# === Agent/model/helper imports (update these paths as needed) ===
try:
    from autogen_ext.agents.web_surfer import MultimodalWebSurfer
except ImportError:
    MultimodalWebSurfer = None
try:
    from autogen_ext.agents.file_surfer import FileSurfer
except ImportError:
    FileSurfer = None
try:
    from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
except ImportError:
    MagenticOneCoderAgent = None
try:
    from autogen_agentchat.agents import CodeExecutorAgent
    from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
except ImportError:
    CodeExecutorAgent = None
    LocalCommandLineCodeExecutor = None
try:
    from autogen_agentchat.teams import MagenticOneGroupChat
except ImportError:
    MagenticOneGroupChat = None
try:
    from agentic_fleet.models.messages import (
        FunctionCall,
        Image,
        MultiModalMessage,
        TaskResult,
        TextMessage,
    )
except ImportError:
    TaskResult = TextMessage = MultiModalMessage = Image = FunctionCall = None


# === Helper functions for message processing (ensure defined before use) ===
def extract_steps_from_content(content: str) -> list[str]:
    """Extract steps from a plan in the content.

    Args:
        content: The content containing the plan

    Returns:
        list[str]: List of extracted steps
    """
    steps: list[str] = []
    if "Here is the plan to follow as best as possible:" in content:
        plan_section = content.split("Here is the plan to follow as best as possible:")[1].strip()
        for line in plan_section.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ")):
                step = line[2:].strip()
                if step:
                    step = re.sub(r"\*\*|\`\`\`|\*", "", step)
                    step = re.sub(r"\s+", " ", step)
                    steps.append(step)
    return steps


async def _handle_image_data(image_data: str | bytes) -> cl.Image | None:
    """Process image data and return a cl.Image element."""
    try:
        if isinstance(image_data, str):
            # Handle base64 encoded image
            if image_data.startswith("data:image"):
                # Extract the base64 part
                header, data = image_data.split(",", 1)
                # Get the image format from the header
                img_format = header.split("/")[1].split(";")[0]
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{img_format}") as f:
                    f.write(base64.b64decode(data))
                    temp_path = f.name
                image = cl.Image(path=temp_path, display="inline")
                # Clean up the temporary file after the image is loaded
                os.unlink(temp_path)
                return image
            if os.path.exists(image_data):
                # Handle file path
                return cl.Image(path=image_data, display="inline")
        elif isinstance(image_data, bytes):
            # Handle raw bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                f.write(image_data)
                temp_path = f.name
            image = cl.Image(path=temp_path, display="inline")
            os.unlink(temp_path)
            return image
    except Exception as e:
        logger.error("Error handling image data: %s", str(e))
    return None


# --- Formatting helpers ---
def format_function_args(args: dict[str, Any]) -> str:
    """Format function arguments for display in the UI.

    Args:
        args: Dictionary of function arguments

    Returns:
        str: Formatted string representation of arguments
    """
    try:
        return json.dumps(args, indent=2)
    except (TypeError, ValueError) as e:
        logger.warning("Failed to format function args: %s", e)
        return str(args)


def format_autogen_function_call(fc_dict: dict[str, str] | Any) -> str:
    """Format Autogen-style function call (dict) for display in the UI.

    Args:
        fc_dict: Function call dictionary with 'name' and 'arguments' keys

    Returns:
        str: Formatted function call string
    """
    if not isinstance(fc_dict, dict):
        return str(fc_dict)  # Fallback if not a dict as expected

    name = fc_dict.get("name", "unknown_function")
    arguments_str = fc_dict.get("arguments", "{}")

    try:
        if isinstance(arguments_str, str):
            arguments_obj = json.loads(arguments_str)
        else:
            arguments_obj = arguments_str
        args_formatted = json.dumps(arguments_obj, indent=2)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug("Failed to parse function call arguments: %s", e)
        args_formatted = str(arguments_str)

    return f"Name: {name}\nArgs:\n{args_formatted}"


# --- Avatar message helper ---
# --- Utility functions for message sanitization and handling ---
def sanitize_html(content: str) -> str:
    """Sanitize HTML content to prevent raw tags from displaying in the UI.

    This removes potentially problematic tags while preserving intended formatting.
    """
    if not content or not isinstance(content, str):
        return str(content or "")

    # Escape HTML entities to prevent injection while preserving intended markdown/formatting
    content = html.escape(content)

    # Convert error tracebacks to formatted blocks
    if "Traceback (most recent call last)" in content:
        parts = content.split("Traceback (most recent call last)")
        result = parts[0]
        for i, part in enumerate(parts[1:]):
            result += f"<details><summary>🐞 <b>Error details</b> (click to expand)</summary><pre>Traceback (most recent call last){part}</pre></details>"
        return result

    return content


def format_agent_name(author: str) -> str:
    """Format agent name for consistent display."""
    if not author or author.lower() in ["unknown", "none", "null"]:
        return "Agent"

    # Remove unique suffixes like UUIDs that sometimes appear in agent names
    author = re.sub(r"_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "", author)

    return author


def clean_error_message(content: str) -> str:
    """Clean error messages for better display in the UI."""
    if not content or not isinstance(content, str):
        return str(content or "")

    # Detect common error patterns
    if (
        "error" in content.lower()
        or "exception" in content.lower()
        or "traceback" in content.lower()
    ):
        # Extract just the main error message when possible
        error_pattern = re.search(r"(?:Error|Exception):\s*([^\n]+)", content)
        if error_pattern:
            return f"🐞 Error: {error_pattern.group(1)}"

    return content


async def _send_message_with_avatar(
    content: str,
    author: str,
    msg: cl.Message | None = None,
    elements_to_add: list[Any] | None = None,
    style: str | None = None,
) -> cl.Message:
    """Helper function to send or update a message with the correct avatar and additional elements."""
    # Sanitize and prepare content
    formatted_author = format_agent_name(author)
    sanitized_content = sanitize_html(content)

    profile_icon_url = cl.user_session.get("profile_icon") or "public/icons/rocket.svg"
    base_elements = [cl.Image(name="avatar", url=profile_icon_url, display="inline", size="small")]
    final_elements = base_elements + elements_to_add if elements_to_add else base_elements

    # Optionally wrap content in a style
    if style:
        sanitized_content = f'<span style="{style}">{sanitized_content}</span>'

    try:
        if msg:
            msg.content = sanitized_content
            msg.author = formatted_author
            msg.elements = final_elements
            await msg.update()
        else:
            await cl.Message(
                content=sanitized_content, author=formatted_author, elements=final_elements
            ).send()
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        # Fall back to a simpler message if there's an error
        await cl.Message(content=f"Message from {formatted_author}: {str(content)[:200]}...").send()


# --- Multimodal content handler ---
@cl.step(type="tool", name="Process Multimodal Content")
async def process_multimodal_content(
    content: list[Any], source_author: str = "Agent"
) -> tuple[str, list[Any] | None]:
    """Process multimodal content from agent responses."""
    try:
        images = []
        text_parts = []
        for item in content:
            if Image is not None and isinstance(item, Image):
                image_data = getattr(item, "data", None) or getattr(item, "content", None)
                if image_data:
                    image_element = await _handle_image_data(image_data)
                    if image_element:
                        images.append(image_element)
            elif isinstance(item, str):
                text_parts.append(item)
            # Add handling for other types if necessary

        combined_text = "\n".join(text_parts).strip()

        if combined_text and images:
            await _send_message_with_avatar(
                content=combined_text, author=source_author, elements_to_add=images
            )
        elif images:
            await _send_message_with_avatar(
                content="📸 Visual content:", author=source_author, elements_to_add=images
            )
        elif combined_text:
            await _send_message_with_avatar(content=combined_text, author=source_author)

        return combined_text, images if images else None

    except Exception as e:
        logger.error(f"Error processing multimodal content: {str(e)}")
        await _send_message_with_avatar(
            content=f"⚠️ Error processing multimodal message: {str(e)}", author="System"
        )


# --- Message parser ---
@cl.step(type="tool")
async def process_message(
    message: Any, collected_responses: list[str], msg: cl.Message | None = None
) -> tuple[str, bool]:
    """Process a single message from an agent."""
    try:
        content = message.content if hasattr(message, "content") else str(message)
        source = getattr(message, "source", "Unknown")

        # Handle different message types
        if TextMessage is not None and isinstance(message, TextMessage):
            # Clean content and send message
            await _send_message_with_avatar(content=content, author=source, msg=msg)
            collected_responses.append(content)

        elif MultiModalMessage is not None and isinstance(message, MultiModalMessage):
            images = [
                await _handle_image_data(image_data)
                for item in message.content
                if (
                    Image is not None
                    and isinstance(item, Image)
                    and (
                        image_data := getattr(item, "data", None) or getattr(item, "content", None)
                    )
                )
            ]
            images = [img for img in images if img]  # Filter out any None values

            if content:
                # Clean content before sending
                cleaned_content = sanitize_html(content)
                if msg:
                    msg.content = cleaned_content
                    msg.author = format_agent_name(source)
                    msg.elements = images
                    await msg.update()
                else:
                    msg = cl.Message(
                        content=cleaned_content, author=format_agent_name(source), elements=images
                    )
                    await msg.send()
                collected_responses.append(content)
            elif images:
                await cl.Message(
                    content=f"📸 Visual content from {format_agent_name(source)}",
                    elements=images,
                    author=format_agent_name(source),
                ).send()

        elif FunctionCall is not None and isinstance(message, FunctionCall):
            # Format function call nicely
            func_args = getattr(message, "args", {})
            func_name = getattr(message, "name", "unknown_function")
            formatted_args = format_function_args(func_args)
            await _send_message_with_avatar(
                content=(
                    f"🛠️ **Function Call**: `{func_name}`\n\n"
                    f"**Arguments**:\n```json\n{formatted_args}\n```"
                ),
                author=source,
                msg=msg,
                style="color:#388e3c;font-weight:bold;",
            )
        else:
            # Clean content and send message
            await _send_message_with_avatar(content=content, author=source, msg=msg)
            collected_responses.append(content)

    except Exception as e:
        # Handle any processing errors gracefully
        error_msg = f"🐞 Error processing message: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())

        # Send a user-friendly error message
        await cl.Message(content=error_msg, author="System").send()
        collected_responses.append(error_msg)

    return content, True


# ... (rest of the code remains the same)


# --- Streaming response parser and display ---
def error_handler(func: Callable) -> Callable:
    """Decorator to handle errors gracefully in async functions."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            # Send a user-friendly error message
            await cl.Message(
                content="🐞 Something went wrong while processing a response. The error has been logged.",
                author="System",
            ).send()

    return wrapper


@error_handler
async def process_response_streaming(
    response: Any, collected_responses: list[str], main_msg: cl.Message
) -> None:
    """
    Enhanced streaming and parsing of each response chunk for Chainlit UI.
    Uses _send_message_with_avatar for new messages to ensure consistent UI.
    """
    source_author = getattr(response, "source", "Agent")

    # Check if response is None or invalid
    if response is None:
        logger.warning("Received None response in process_response_streaming")
        return

    # --- TaskResult: stream and parse each message, show stop reason ---
    if TaskResult is not None and isinstance(response, TaskResult):
        for msg_item in response.messages:
            item_source = getattr(msg_item, "source", source_author)

            class TempResponse:
                pass

            actual_item_to_process = msg_item
            if not hasattr(msg_item, "source"):
                temp_resp = TempResponse()
                temp_resp.content = msg_item
                temp_resp.source = item_source
                actual_item_to_process = temp_resp
            await process_response_streaming(actual_item_to_process, collected_responses, main_msg)

        if response.stop_reason:
            await _send_message_with_avatar(
                content=f"🛑 Task stopped: {response.stop_reason}",
                author="System",
                style="color:#b71c1c;font-weight:bold;",
            )
        return

    # --- Autogen-style function_call attribute (dict) ---
    if (
        hasattr(response, "function_call")
        and isinstance(response.function_call, dict)
        and not isinstance(response, FunctionCall)
    ):
        formatted_fc = format_autogen_function_call(response.function_call)
        await _send_message_with_avatar(
            content=f"🛠️ <span style='color:#1976d2;font-weight:bold;'>Function Call (dict)</span>:<br><pre style='background:#f5f5f5;border-radius:6px;padding:8px;'>{formatted_fc}</pre>",
            author=source_author,
        )
        return

    # --- FunctionCall type (tool call) ---
    if FunctionCall is not None and isinstance(response, FunctionCall):
        function_name = getattr(response, "name", "UnknownFunction")
        args_formatted = format_function_args(getattr(response, "args", {}))
        await _send_message_with_avatar(
            content=f"🛠️ <span style='color:#388e3c;font-weight:bold;'>Tool Call</span>: <code>{function_name}</code><br>Args:<br><pre style='background:#f5f5f5;border-radius:6px;padding:8px;'>{args_formatted}</pre>",
            author=getattr(response, "source", "Tool"),
        )
        return

    # --- Inner thought ---
    if hasattr(response, "inner_monologue") and response.inner_monologue:
        await _send_message_with_avatar(
            content=f"💭 <i>{response.inner_monologue}</i>",
            author=source_author,
            style="color:#616161;font-style:italic;",
        )
        return

    # --- MultiModalMessage ---
    if MultiModalMessage is not None and isinstance(response, MultiModalMessage):
        images_elements = []
        text_content_parts = []
        for item_idx, item_content in enumerate(response.content):
            if Image is not None and isinstance(item_content, Image):
                image_data = getattr(item_content, "data", None) or getattr(
                    item_content, "content", None
                )
                if image_data:
                    img_element = await _handle_image_data(image_data)
                    if img_element:
                        img_element.name = f"image_{item_idx}_{int(time.time())}"
                        images_elements.append(img_element)
            elif isinstance(item_content, str):
                text_content_parts.append(item_content)
            elif hasattr(item_content, "text"):
                text_content_parts.append(getattr(item_content, "text"))
        full_text_content = "\n".join(text_content_parts).strip()
        if full_text_content or images_elements:
            await _send_message_with_avatar(
                content=(
                    ("📸 <b>Visual content</b><br>" + full_text_content)
                    if full_text_content
                    else "📸 <b>Visual content</b>"
                ),
                author=source_author,
                elements_to_add=images_elements if images_elements else None,
                style="color:#6d4c41;",
            )
            if full_text_content:
                collected_responses.append(full_text_content)
        return

    # --- TextMessage ---
    if TextMessage is not None and isinstance(response, TextMessage):
        content = getattr(response, "content", str(response))
        author = format_agent_name(source_author)

        # Clean content to prevent HTML/traceback issues
        sanitized_content = sanitize_html(content)

        if author.lower() == "user":
            style = "color:#1976d2;"
            await _send_message_with_avatar(content=sanitized_content, author="User", style=style)
        elif author.lower() == "system":
            style = "color:#616161;"
            await _send_message_with_avatar(content=sanitized_content, author="System", style=style)
        else:
            style = "color:#388e3c;"
            await _send_message_with_avatar(content=sanitized_content, author=author, style=style)

        collected_responses.append(content)
        return

    # --- If response has chat_message attribute ---
    if hasattr(response, "chat_message"):
        chat_msg_content = response.chat_message
        chat_msg_source = getattr(chat_msg_content, "source", source_author)
        await process_response_streaming(chat_msg_content, collected_responses, main_msg)
        return

    # --- If response is a list/tuple ---
    if isinstance(response, (list, tuple)):
        for item_in_list in response:
            item_source = getattr(item_in_list, "source", source_author)

            class TempItemResponse:
                pass

            actual_item_to_process = item_in_list
            if not hasattr(item_in_list, "source"):
                temp_resp = TempItemResponse()
                if isinstance(item_in_list, str):
                    temp_resp.content = item_in_list
                elif isinstance(item_in_list, dict) and "content" in item_in_list:
                    temp_resp.content = item_in_list["content"]
                else:
                    temp_resp.content = str(item_in_list)
                temp_resp.source = item_source
                actual_item_to_process = temp_resp
            await process_response_streaming(actual_item_to_process, collected_responses, main_msg)
        return

    # --- Fallback: display as plain text with type info ---
    content_str = str(response)
    if content_str:
        await _send_message_with_avatar(
            content=f"⚠️ <b>Unparsed response</b> (type: {type(response).__name__}):<br><pre style='background:#fff3e0;border-radius:6px;padding:8px;'>{content_str}</pre>",
            author="System",
            style="color:#b71c1c;",
        )
        collected_responses.append(content_str)


@cl.on_settings_update
async def handle_settings_update(settings: dict[str, Any]) -> None:
    """Handle chat settings updates."""
    try:
        # Store new settings in session
        cl.user_session.set("max_rounds", settings.get("max_rounds", DEFAULT_MAX_ROUNDS))
        cl.user_session.set("max_time", settings.get("max_time", DEFAULT_MAX_TIME))
        cl.user_session.set("max_stalls", settings.get("max_stalls", DEFAULT_MAX_STALLS))
        cl.user_session.set("start_page", settings.get("start_page", DEFAULT_START_PAGE))

        # Notify the user
        await cl.Message(content="✅ Settings updated successfully", author="System").send()
    except Exception as e:
        logger.error("Settings update error: %s", str(e))
        await cl.Message(content=f"⚠️ Failed to update settings: {str(e)}", author="System").send()


@cl.action_callback("reset_chat")
async def on_action_reset(action: cl.Action) -> None:
    """Handle reset action."""
    try:
        await on_chat_stop()
        await on_chat_start()
        await cl.Message(content="Chat has been reset.", author="System").send()
    except Exception as e:
        logger.error("Error resetting chat: %s", str(e))
        await cl.Message(
            content="⚠️ Failed to reset chat. Please try again.", author="System"
        ).send()


async def list_available_mcps() -> list[dict[str, Any]]:
    """List available MCP tools.

    Returns:
        list[dict]: List of MCP server configurations
    """
    # TODO: Implement actual MCP server discovery
    return []


@cl.action_callback("list_mcp_tools")
async def on_action_list_mcp(_: cl.Action) -> None:
    """Handle list MCP tools action."""
    try:
        mcp_servers = await list_available_mcps()
        if mcp_servers:
            message = "## Available MCP Tools\n\n"
            for i, server in enumerate(mcp_servers):
                message += f"### {i+1}. {server.get('name', 'Unnamed Server')}\n"
                message += f"- **URL**: {server.get('url', 'No URL')}\n"
                if "description" in server:
                    message += f"- **Description**: {server['description']}\n"
                message += "\n"

            await cl.Message(content=message, author="System").send()
        else:
            await cl.Message(content="No MCP tools available", author="System").send()

        # Store the servers in the session for later use
        cl.user_session.set("mcp_servers", mcp_servers)

    except Exception as e:
        error_msg = f"⚠️ Error retrieving MCP configurations: {str(e)}"
        logger.error("Error listing MCP configurations: %s", traceback.format_exc())
        await cl.Message(content=error_msg, author="System").send()


@cl.on_stop
async def on_chat_stop() -> None:
    """Clean up resources when the chat is stopped."""
    try:
        # Clean up application resources
        app_ctx = cl.user_session.get("app_context")
        if app_ctx and hasattr(app_ctx, "cleanup"):
            await app_ctx.cleanup()

        # Clean up agent team resources
        team = cl.user_session.get("team")
        if team and hasattr(team, "cleanup"):
            await team.cleanup()

        # Clean up workspace
        workspace_dir = os.path.join(os.getcwd(), "workspace")
        if os.path.exists(workspace_dir):
            shutil.rmtree(workspace_dir, ignore_errors=True)

        # Reset session values
        session_keys = [
            "chat_profile",
            "profile_type",
            "agent_team",
            "profile_icon",
            "settings",
            "mcp_servers",
            "team",
            "task_list",
            "max_rounds",
            "max_time",
            "max_stalls",
            "start_page",
        ]
        for key in session_keys:
            try:
                cl.user_session.set(key, None)
            except Exception as e:
                logger.warning(f"Failed to reset session key {key}: {str(e)}")

        logger.info("Chat session stopped and resources cleaned up")
    except Exception as e:
        logger.error(f"Chat stop error: {str(e)}")


@cl.on_chat_start
async def on_chat_start():
    """Initialize a new chat session with proper setup and welcome message."""
    try:
        # Initialize session state
        cl.user_session.set("chat_history", [])
        cl.user_session.set("is_processing", False)
        cl.user_session.set("message_id", str(uuid.uuid4()))

        # Send welcome message with action buttons
        welcome_msg = """# 👋 Welcome to AgenticFleet!

I'm your AI assistant. Here's what I can help you with:
- Answering questions
- Assisting with tasks
- Providing information
- And much more!

How can I assist you today?"""

        # Create and send welcome message with actions
        actions = [
            cl.Action(name="help", value="help", label="❓ Help", payload={"action": "help"}),
            cl.Action(
                name="examples",
                value="examples",
                label="💡 Examples",
                payload={"action": "examples"},
            ),
            cl.Action(
                name="settings",
                value="settings",
                label="⚙️ Settings",
                payload={"action": "settings"},
            ),
        ]

        await cl.Message(content=welcome_msg, actions=actions).send()

        logger.info(f"New chat session started: {cl.user_session.get('message_id')}")

    except Exception as e:
        error_msg = f"Error initializing chat session: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await cl.Error(
            name="Initialization Error",
            description="Failed to initialize the chat session. Please refresh the page and try again.",
            display="page",
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages with proper error handling and response generation."""
    # Skip processing if another message is being processed
    if cl.user_session.get("is_processing", False):
        return

    # Set processing flag
    cl.user_session.set("is_processing", True)

    try:
        # Get or initialize chat history
        chat_history = cl.user_session.get("chat_history", [])

        # Process the user's message
        user_message = message.content.strip()
        if not user_message:
            await cl.Message(content="Please enter a valid message.").send()
            return

        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_message})

        # Create a step to track the message processing
        async with cl.Step(name="Processing Message", type="llm") as step:
            step.input = user_message

            # Generate response (placeholder for actual response generation)
            response = await generate_response(user_message, chat_history)

            # Update step with results
            step.output = response

            # Send the response
            await cl.Message(content=response).send()

            # Update chat history
            chat_history.append({"role": "assistant", "content": response})
            cl.user_session.set("chat_history", chat_history)

    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await cl.Error(
            name="Processing Error",
            description="An error occurred while processing your message. Please try again.",
            display="toast",
        ).send()
    finally:
        # Always reset the processing flag
        cl.user_session.set("is_processing", False)


async def generate_response(user_message: str, chat_history: list[dict]) -> str:
    """Generate a response to the user's message.

    Args:
        user_message: The user's message
        chat_history: The chat history

    Returns:
        str: The generated response
    """
    # This is a placeholder for the actual response generation logic
    # In a real implementation, you would call your LLM or other services here

    # For demonstration, we'll just echo the message with some processing
    return f"I received your message: {user_message}. This is a placeholder response."


def main() -> None:
    """Run the Chainlit application."""
    host: str = os.environ.get("CHAINLIT_HOST", "0.0.0.0")
    port_env: str = os.environ.get("CHAINLIT_PORT", "8080")
    try:
        port: int = int(port_env)
        if not (0 < port < 65536):
            port = 8080
    except ValueError:
        port = 8080
    logger.info(f"Starting Chainlit UI on {host}:{port}")
    try:
        from chainlit.cli import run_chainlit

        run_chainlit(os.path.abspath(__file__))
    except ImportError:
        result = subprocess.run(
            [
                "chainlit",
                "run",
                os.path.abspath(__file__),
                "--host",
                host,
                "--port",
                str(port),
                "--no-cache",
            ],
            check=True,
        )
        sys.exit(result.returncode)
    except Exception as e:
        logger.error(f"Failed to start Chainlit: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
