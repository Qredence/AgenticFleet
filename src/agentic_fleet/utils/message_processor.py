"""
Message processing utilities for AgenticFleet.

This module implements a middleware-based message processing pipeline
to standardize message handling throughout the application.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

import chainlit as cl

from agentic_fleet.models import Response, TextMessage
from agentic_fleet.utils.error_handling import with_error_handling

logger = logging.getLogger(__name__)

# Type definitions
Context = Dict[str, Any]
Middleware = Callable[[Context], Awaitable[Context]]
T = TypeVar("T")


class MessageProcessor:
    """
    A middleware-based message processing pipeline.

    This class provides a flexible way to process messages through a series of middleware
    components that can modify the message, add context, or handle specific message types.
    """

    def __init__(self):
        """Initialize a new message processor with an empty middleware stack."""
        self.middleware: List[Middleware] = []

    def add_middleware(self, middleware: Middleware) -> None:
        """
        Add middleware to the processing pipeline.

        Args:
            middleware: Async function that takes and returns a context dictionary
        """
        self.middleware.append(middleware)

    async def process(self, message: Any, initial_context: Optional[Dict[str, Any]] = None) -> Context:
        """
        Process a message through the middleware pipeline.

        Args:
            message: The message to process
            initial_context: Optional initial context dictionary

        Returns:
            Context: The final context after processing
        """
        # Initialize context with message and defaults
        context = initial_context or {}
        context["message"] = message
        context["response"] = None
        context["error"] = False
        context["stop_processing"] = False

        # Process through middleware pipeline
        for middleware in self.middleware:
            # Skip processing if a middleware requested to stop
            if context.get("stop_processing", False):
                break

            # Apply middleware with error handling
            context = await with_error_handling(middleware, context)

        return context


# Common middleware implementations


async def authentication_middleware(context: Context) -> Context:
    """
    Verify user authentication before processing.

    Args:
        context: The processing context

    Returns:
        Context: Updated context
    """
    message = context["message"]

    # Check if authentication is required and present
    if not getattr(message, "is_authenticated", True):
        context["response"] = Response(content="Authentication required", error=True)
        context["stop_processing"] = True

    return context


async def logging_middleware(context: Context) -> Context:
    """
    Log message details for debugging and monitoring.

    Args:
        context: The processing context

    Returns:
        Context: Updated context
    """
    message = context["message"]

    if hasattr(message, "content"):
        logger.debug(f"Processing message: {message.content[:100]}...")
    else:
        logger.debug(f"Processing message of type: {type(message).__name__}")

    return context


async def agent_routing_middleware(context: Context) -> Context:
    """
    Route messages to appropriate agents based on content.

    Args:
        context: The processing context

    Returns:
        Context: Updated context with agent selection
    """
    # This would typically use a more sophisticated routing algorithm
    message = context["message"]

    # Simple keyword-based routing example
    if hasattr(message, "content"):
        content = getattr(message, "content", "").lower()

        if "code" in content or "function" in content or "script" in content:
            context["agent_type"] = "coding"
        elif "search" in content or "find" in content or "look up" in content:
            context["agent_type"] = "web_search"
        elif "think" in content or "reason" in content or "analyze" in content:
            context["agent_type"] = "reasoning"
        else:
            context["agent_type"] = "default"

    return context


async def response_formatting_middleware(context: Context) -> Context:
    """
    Format responses for UI display.

    Args:
        context: The processing context

    Returns:
        Context: Updated context with formatted response
    """
    response = context.get("response")

    if response is None:
        return context

    # Customize response formatting based on type
    if isinstance(response, Response):
        if response.error:
            context["formatted_response"] = f"⚠️ {response.content}"
        else:
            context["formatted_response"] = response.content
    elif isinstance(response, list):
        context["formatted_response"] = "\n".join(str(item) for item in response)
    else:
        context["formatted_response"] = str(response)

    return context


async def send_response_middleware(context: Context) -> Context:
    """
    Send the response to the UI.

    Args:
        context: The processing context

    Returns:
        Context: Updated context
    """
    if context.get("error", False):
        # Error has occurred and was handled
        error_id = context.get("error_id", "unknown")
        error_msg = context.get("error_message", "An unknown error occurred")

        await cl.Message(content=f"⚠️ Something went wrong (Error ID: {error_id}). Our team has been notified.").send()
        return context

    response = context.get("response")
    if response is None:
        return context

    formatted_response = context.get("formatted_response", str(response))

    # Send the formatted response
    await cl.Message(content=formatted_response).send()

    return context


# Factory function to create a standard message processor


def create_standard_processor() -> MessageProcessor:
    """
    Create a message processor with standard middleware configuration.

    Returns:
        MessageProcessor: Configured message processor
    """
    processor = MessageProcessor()

    # Add standard middleware in execution order
    processor.add_middleware(logging_middleware)
    processor.add_middleware(authentication_middleware)
    processor.add_middleware(agent_routing_middleware)
    processor.add_middleware(response_formatting_middleware)
    processor.add_middleware(send_response_middleware)

    return processor
