"""
Middleware for authentication.
"""

import logging
from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED

# Initialize logging
logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authenticating requests."""

    def __init__(self, app, api_key: str | None = None, exclude_paths: list | None = None):
        """
        Initialize the authentication middleware.

        Args:
            app: The FastAPI application
            api_key: The API key to validate against
            exclude_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        self.api_key = api_key
        self.exclude_paths = exclude_paths or ["/api/docs", "/api/redoc", "/api/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and authenticate it.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from the next middleware or route handler
        """
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Skip authentication if no API key is configured
        if not self.api_key:
            return await call_next(request)

        # Get the API key from the request
        api_key = request.headers.get("X-API-Key")

        # Validate the API key
        if not api_key or api_key != self.api_key:
            logger.warning(
                f"Unauthorized access attempt: {request.method} {request.url.path} "
                f"Client: {request.client.host if request.client else 'Unknown'}"
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key"
            )

        # API key is valid, proceed with the request
        return await call_next(request)
