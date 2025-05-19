"""
Main FastAPI application for the Agentic Fleet API.
"""

import logging
import os
import platform
import sys
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agentic_fleet.api.middleware import LoggingMiddleware
from agentic_fleet.api.routes import agents, chat, tasks
from agentic_fleet.database.session import get_db
from agentic_fleet.exceptions import AgenticFleetAPIError, AgenticFleetDatabaseError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agentic_fleet")

# Create FastAPI app
app = FastAPI(
    title="Agentic Fleet API",
    description="API for managing AI agents and their tasks",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers


@app.exception_handler(AgenticFleetAPIError)
async def api_exception_handler(request: Request, exc: AgenticFleetAPIError) -> JSONResponse:
    """
    Handle API exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(AgenticFleetDatabaseError)
async def database_exception_handler(
    request: Request, exc: AgenticFleetDatabaseError
) -> JSONResponse:
    """
    Handle database exceptions.
    """
    logger.error(f"Database error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(agents, prefix="/agents", tags=["agents"])
app.include_router(tasks, prefix="/tasks", tags=["tasks"])
app.include_router(chat, prefix="/chat", tags=["chat"])


@app.get("/")
async def root() -> dict[str, Any]:
    """
    Root endpoint that returns API information.
    """
    return {
        "name": "Agentic Fleet API",
        "version": app.version,
        "description": app.description,
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Health check endpoint.

    Checks if the database connection is working and returns system information.
    """
    # Check database connection
    try:
        # Try to execute a simple query to check database connection
        await db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "disconnected"

    # Get system information
    system_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "time": datetime.now().isoformat(),
    }

    # Get environment information
    env = os.environ.get("ENVIRONMENT", "development")

    return {
        "status": "healthy",
        "database": db_status,
        "environment": env,
        "system": system_info,
        "api_version": app.version,
    }
