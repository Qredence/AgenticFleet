"""Message processing service for AgenticFleet.

This module provides functionality for processing and streaming messages in the chat interface.
"""

from typing import Any

import chainlit as cl
from autogen_agentchat.messages import TextMessage

# Task status constants
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"


async def stream_text(text: str, delay: float = 0.03) -> None:
    """Stream text with a delay between characters."""
    msg = cl.Message(content="")
    await msg.send()
    for char in text:
        await msg.stream_token(char)
    await msg.update()


async def process_response(
    response: TextMessage | list[Any] | dict[str, Any],
) -> tuple[str | None, str | None]:
    """Process agent responses and return response text and plan update.

    Args:
        response: The response from the agent, which can be a TextMessage, list, or dict

    Returns:
        A tuple containing the response text and plan update (if any)
    """
    response_text = None
    plan_update = None

    try:
        if isinstance(response, TextMessage):
            response_text = response.content
            # Check if this is a plan update
            if "Here is the plan to follow as best as possible:" in response_text:
                plan_parts = response_text.split("Here is the plan to follow as best as possible:")
                if len(plan_parts) > 1:
                    plan_update = plan_parts[1].strip()

            await cl.Message(content=response_text, author=response.source).send()
        elif isinstance(response, (list, tuple)):
            for item in response:
                item_text, item_plan = await process_response(item)
                if item_text:
                    response_text = item_text
                if item_plan:
                    plan_update = item_plan
        elif isinstance(response, dict):
            if "content" in response:
                response_text = response["content"]
                await cl.Message(content=response_text).send()
            else:
                response_text = str(response)
                await cl.Message(content=response_text).send()
        else:
            response_text = str(response)
            await cl.Message(content=response_text).send()
    except Exception as e:
        error_msg = f"⚠️ Error processing response: {str(e)}"
        await cl.Message(content=error_msg).send()

    return response_text, plan_update
