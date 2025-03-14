"""
Main entry point for the Agentic Fleet application.
"""

import logging
import os

import uvicorn
from dotenv import load_dotenv

from agentic_fleet.api.app import app
from agentic_fleet.database.session import create_tables

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agentic_fleet")


def main():
    """
    Main function to run the application.
    """
    # Initialize database
    create_tables()
    logger.info("Database tables created")

    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "False").lower() == "true"

    logger.info(f"Starting Agentic Fleet API on {host}:{port}")

    # Run the application
    uvicorn.run(
        "agentic_fleet.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
