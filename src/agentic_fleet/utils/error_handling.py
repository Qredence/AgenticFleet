"""
Standardized error handling utilities for AgenticFleet.

This module provides a consistent approach to error handling throughout the codebase,
including a custom exception hierarchy and utility functions for safe execution.
"""

import functools
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

import chainlit as cl

from agentic_fleet.models import Response

logger = logging.getLogger(__name__)

# Type variables for function signatures
T = TypeVar("T")
R = TypeVar("R")


class AgenticFleetError(Exception):
    """Base exception for all AgenticFleet errors."""

    def __init__(self, message: str, *args: Any):
        self.message = message
        super().__init__(message, *args)


class ConfigurationError(AgenticFleetError):
    """Raised when there is an issue with configuration settings."""


class AgentError(AgenticFleetError):
    """Base exception for agent-related errors."""


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize."""


class AgentExecutionError(AgentError):
    """Raised when an agent fails during execution."""


class MessageProcessingError(AgenticFleetError):
    """Raised when message processing fails."""


class DatabaseError(AgenticFleetError):
    """Raised when database operations fail."""


class ToolError(AgenticFleetError):
    """Raised when a tool operation fails."""


class APIError(AgenticFleetError):
    """Raised when API operations fail."""


class AuthenticationError(AgenticFleetError):
    """Raised when authentication fails."""


class CancellationError(AgenticFleetError):
    """Raised when an operation is cancelled."""


async def safe_execute(
    func: Callable[..., Any],
    *args: Any,
    error_prefix: str = "",
    log_exception: bool = True,
    **kwargs: Any,
) -> Response:
    """
    Safely execute a function and handle any exceptions.

    Args:
        func: The function to execute
        *args: Arguments to pass to the function
        error_prefix: Optional prefix for error messages
        log_exception: Whether to log exceptions (defaults to True)
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Response: The result wrapped in a Response object or an error Response
    """
    prefix = f"{error_prefix}: " if error_prefix else ""
    try:
        result = await func(*args, **kwargs)
        if isinstance(result, Response):
            return result
        return Response(content=result)
    except AgenticFleetError as e:
        if log_exception:
            logger.warning(
                f"{prefix}Operation failed with {e.__class__.__name__}: {str(e)}",
                exc_info=True,
            )
        return Response(content=f"Error: {str(e)}", error=True)
    except Exception as e:
        if log_exception:
            logger.error(
                f"{prefix}Unexpected error in {func.__name__}: {str(e)}",
                exc_info=True,
            )
        return Response(
            content="An unexpected error occurred. Please try again or contact support.",
            error=True,
        )


def exception_handler(
    exception_type: Type[Exception] = Exception,
    fallback_value: Optional[Any] = None,
    log_level: int = logging.ERROR,
    reraise: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Union[T, Any]]]:
    """
    Decorator to handle exceptions in functions.

    Args:
        exception_type: Type of exception to catch
        fallback_value: Value to return if an exception occurs
        log_level: Logging level for exceptions
        reraise: Whether to reraise the exception after logging

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                logger.log(
                    log_level,
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True,
                )
                if reraise:
                    raise
                return fallback_value

        return wrapper

    return decorator


async def with_error_handling(
    func: Callable[..., Any], context: Dict[str, Any], *args: Any, **kwargs: Any
) -> Dict[str, Any]:
    """
    Execute a function with context-aware error handling for middleware pipelines.

    Args:
        func: The function to execute
        context: The context dictionary
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Dict[str, Any]: Updated context
    """
    try:
        return await func(context, *args, **kwargs)
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Error [{error_id}] in middleware: {str(e)}", exc_info=True)
        
        # Update context with error information
        context["error"] = True
        context["error_id"] = error_id
        context["error_message"] = str(e)
        context["stop_processing"] = True
        
        return context


async def send_error_message(error: Exception, user_friendly: bool = True) -> None:
    """
    Send an error message to the UI with appropriate details.

    Args:
        error: The exception that occurred
        user_friendly: Whether to show a user-friendly message (vs technical details)
    """
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Error [{error_id}]: {str(error)}", exc_info=True)
    
    if user_friendly:
        await cl.Message(
            content=f"⚠️ Something went wrong (Error ID: {error_id}). Our team has been notified."
        ).send()
    else:
        # For development environments, show more details
        error_details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await cl.Message(
            content=f"⚠️ Error (ID: {error_id}):\n```\n{str(error)}\n\n{error_details}\n```"
        ).send()


def convert_exception(
    from_exception: Type[Exception], to_exception: Type[Exception]
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to convert one exception type to another.

    Args:
        from_exception: Exception type to convert from
        to_exception: Exception type to convert to

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except from_exception as e:
                raise to_exception(str(e)) from e

        return wrapper

    return decorator 