"""API runner module for AgenticFleet."""

import logging
import os
from argparse import Namespace
from typing import Any

import uvicorn

from agentic_fleet.core.application.context import ApplicationContext
from agentic_fleet.database.session import create_tables

logger = logging.getLogger(__name__)


def run(app_context: ApplicationContext, args: Namespace) -> None:
    """Run the API server.
    
    Args:
        app_context: Application context
        args: Command-line arguments
    """
    logger.info("Starting API server")
    
    # Initialize database
    create_tables()
    logger.info("Database tables created")
    
    # Get host and port from args or environment
    host = args.host or os.environ.get("HOST", "0.0.0.0")
    port = args.port or int(os.environ.get("PORT", "8000"))
    reload = args.reload or os.environ.get("RELOAD", "False").lower() == "true"
    
    logger.info(f"Starting Agentic Fleet API on {host}:{port}")
    
    # Run the application
    uvicorn.run(
        "agentic_fleet.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
