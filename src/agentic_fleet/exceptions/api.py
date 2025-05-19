"""
API-specific exceptions for Agentic Fleet.
"""

from typing import Any

from agentic_fleet.exceptions.base import AgenticFleetAPIError


class NotFoundError(AgenticFleetAPIError):
    """
    Exception raised when a requested resource is not found.
    """

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class ValidationError(AgenticFleetAPIError):
    """
    Exception raised when request validation fails.
    """

    def __init__(self, message: str = "Validation error", errors: dict[str, Any] | None = None):
        self.errors = errors or {}
        super().__init__(message=message, status_code=422)


class AuthenticationError(AgenticFleetAPIError):
    """
    Exception raised when authentication fails.
    """

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(AgenticFleetAPIError):
    """
    Exception raised when a user is not authorized to perform an action.
    """

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message=message, status_code=403)


class RateLimitError(AgenticFleetAPIError):
    """
    Exception raised when a rate limit is exceeded.
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(message=message, status_code=429)
