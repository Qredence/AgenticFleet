"""Message processing module for AgenticFleet."""

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import chainlit as cl
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import (
    FunctionCall,
    Image,
    MultiModalMessage,
    TextMessage,
)
from chainlit import Message, Step, TaskList, TaskStatus, context, sleep, user_session

# Constants for task status
TASK_STATUS_RUNNING = TaskStatus.RUNNING
TASK_STATUS_COMPLETED = TaskStatus.DONE
TASK_STATUS_FAILED = TaskStatus.FAILED

logger = logging.getLogger(__name__)


async def stream_text(
    text: str, stream_delay: float = 0.01
) -> AsyncGenerator[str, None]:
    """Stream text content as a single chunk."""
    await asyncio.sleep(stream_delay)
    yield text


@cl.step(name="Response Processing", type="process", show_input=True)
async def process_response(
    response: Union[TaskResult, TextMessage, List[Any], Dict[str, Any]],
    collected_responses: List[str],
) -> None:
    """Process agent responses with step visualization and error handling."""
    try:
        current_step = context.current_step
        current_step.input = str(response)

        if isinstance(response, TaskResult):
            async with cl.Step(
                name="Task Execution", type="task", show_input=True, language="json"
            ) as task_step:
                task_step.input = getattr(response, "task", "Task execution")
                for msg in response.messages:
                    await process_message(msg, collected_responses)
                if response.stop_reason:
                    task_step.output = f"Task stopped: {response.stop_reason}"
                    task_step.is_error = True
                    await Message(
                        content=f"🛑 {task_step.output}", author="System"
                    ).send()

        elif isinstance(response, TextMessage):
            source = getattr(response, "source", "Unknown")
            async with cl.Step(
                name=f"Agent: {source}", type="message", show_input=True
            ) as msg_step:
                msg_step.input = response.content
                await process_message(response, collected_responses)
                msg_step.output = f"Message from {source} processed"

        elif hasattr(response, "chat_message"):
            async with cl.Step(
                name="Chat Message", type="message", show_input=True
            ) as chat_step:
                chat_step.input = str(response.chat_message)
                await process_message(response.chat_message, collected_responses)
                chat_step.output = "Chat message processed"

        elif hasattr(response, "inner_monologue"):
            async with cl.Step(
                name="Inner Thought", type="reasoning", show_input=True
            ) as thought_step:
                thought_step.input = str(response.inner_monologue)
                await process_message(response.inner_monologue, collected_responses)
                thought_step.output = "Inner thought processed"

        elif hasattr(response, "function_call"):
            async with cl.Step(
                name="Function Call", type="function", show_input=True, language="json"
            ) as func_step:
                func_step.input = str(response.function_call)
                collected_responses.append(str(response.function_call))
                func_step.output = "Function call processed"

        elif isinstance(response, (list, tuple)):
            for item in response:
                await process_response(item, collected_responses)

        else:
            collected_responses.append(str(response))
            current_step.output = "Unknown response type processed"

    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        await Message(content=f"⚠️ Error processing response: {str(e)}").send()


@cl.step(name="Message Processing", type="message", show_input=True)
async def process_message(
    message: Union[TextMessage, Any], collected_responses: List[str]
) -> None:
    """Process a single message with proper formatting and step visualization."""
    try:
        current_step = context.current_step
        # Extract content and source
        content = message.content if hasattr(message, "content") else str(message)
        source = getattr(message, "source", "Unknown")
        current_step.input = content

        # Check for plan and update task list
        steps = extract_steps_from_content(content)
        if steps:
            async with cl.Step(
                name="Plan Creation",
                type="planning",
                show_input=True,
                language="markdown",
            ) as plan_step:
                plan_step.input = content
                task_list = user_session.get("task_list")
                if task_list:
                    task_list.tasks.clear()
                    task_list.status = "Creating tasks..."
                    await task_list.send()

                    # Add tasks with delays for visual feedback
                    for step in steps:
                        task = cl.Task(
                            title=step["title"],
                            status=TaskStatus.READY,
                            description=step.get("description"),
                        )
                        await task_list.add_task(task)
                        await sleep(0.2)

                    task_list.status = "Ready to execute..."
                    await task_list.send()
                    plan_step.output = f"Created plan with {len(steps)} steps"

        # Format content based on message type
        if isinstance(message, TextMessage):
            step_name = f"Message from {source}"
            async with Step(name=step_name, type="message") as msg_step:
                msg_step.input = content
                msg = Message(content="", author=source)
                async for chunk in stream_text(content):
                    await msg.stream_token(chunk)
                await msg.send()
                collected_responses.append(content)
                msg_step.output = "Message processed"

        elif isinstance(message, MultiModalMessage):
            async with Step(name="Multimodal Processing", type="media") as media_step:
                media_step.input = "Processing multimodal message"
                await _process_multimodal_message(message.content)
                media_step.output = "Multimodal content processed"

        elif isinstance(message, FunctionCall):
            async with Step(
                name=f"Function: {message.name}", type="function"
            ) as func_step:
                func_step.input = json.dumps(message.args, indent=2)
                await Message(
                    content=f"🛠️ Function: {message.name}\nArgs: {json.dumps(message.args, indent=2)}",
                    author=source,
                    indent=1,
                ).send()
                func_step.output = "Function call processed"

        else:
            async with Step(name="Generic Message", type="other") as gen_step:
                gen_step.input = content
                msg = Message(content="", author="System")
                async for chunk in stream_text(content):
                    await msg.stream_token(chunk)
                await msg.send()
                collected_responses.append(content)
                gen_step.output = "Message processed"

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await Message(content=f"⚠️ Error processing message: {str(e)}").send()


def extract_steps_from_content(content: str) -> List[Dict[str, str]]:
    """Extract steps from the content with their descriptions.

    Returns:
        List of dictionaries with 'title' and 'description' keys
    """
    steps = []
    if "Here is the plan to follow as best as possible:" in content:
        plan_section = content.split("Here is the plan to follow as best as possible:")[
            1
        ].strip()
        current_step = None

        for line in plan_section.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith(("• ", "- ", "* ")):
                if current_step:
                    steps.append(current_step)

                step_text = line[2:].strip()
                step_text = re.sub(r"\*\*|\`\`\`|\*", "", step_text)
                step_text = re.sub(r"\s+", " ", step_text)

                current_step = {"title": step_text, "description": ""}
            elif current_step:
                if current_step["description"]:
                    current_step["description"] += " "
                current_step["description"] += line

        if current_step:
            steps.append(current_step)

    return steps


async def _process_multimodal_message(content: List[Any]) -> None:
    """Process a multimodal message containing text and images."""
    try:
        for item in content:
            if isinstance(item, Image):
                image_data = getattr(item, "data", None) or getattr(
                    item, "content", None
                )
                if image_data:
                    await _handle_image_data(image_data)

    except Exception as e:
        logger.error(f"Error processing multimodal message: {str(e)}")
        await Message(content=f"⚠️ Error processing multimodal message: {str(e)}").send()


async def _handle_image_data(image_data: Union[str, bytes]) -> Optional[Image]:
    """Handle image data processing and display."""
    try:
        if isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                image = Image(url=image_data, display="inline")
                await Message(content="📸 New screenshot:", elements=[image]).send()
                return image
            elif os.path.isfile(image_data):
                image = Image(path=image_data, display="inline")
                await Message(content="📸 New screenshot:", elements=[image]).send()
                return image
        elif isinstance(image_data, bytes):
            from agentic_fleet.config import config_manager

            env_config = config_manager.get_environment_settings()
            debug_dir = os.path.join(env_config["logs_dir"], "debug")
            os.makedirs(debug_dir, exist_ok=True)
            temp_path = os.path.join(debug_dir, f"screenshot_{int(time.time())}.png")
            with open(temp_path, "wb") as f:
                f.write(image_data)
            image = Image(path=temp_path, display="inline")
            await Message(content="📸 New screenshot:", elements=[image]).send()
            return image

    except Exception as e:
        logger.error(f"Error handling image data: {str(e)}")
        await Message(content=f"⚠️ Error handling image: {str(e)}").send()

    return None
