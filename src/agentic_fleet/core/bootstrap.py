# src/agentic_fleet/core/bootstrap.py
"""Bootstrap module for AgenticFleet."""

import logging
from pathlib import Path

from dotenv import load_dotenv

from agentic_fleet.config import config_manager
from agentic_fleet.core.application.context import ApplicationContext
from agentic_fleet.core.application.manager import ApplicationManager
from agentic_fleet.database.session import initialize_database
from agentic_fleet.services.client_factory import create_client as create_default_client

logger = logging.getLogger(__name__)

def bootstrap_application(config_dir: Path | None = None) -> ApplicationContext:
    """Bootstrap the application.
    
    Args:
        config_dir: Directory containing configuration files
        
    Returns:
        Application context
    """
    # Load environment variables
    load_dotenv()

    # Initialize configuration
    if config_dir:
        config_manager.config_dir = config_dir
    config_manager.load_all()

    # Configure logging
    logging_config = config_manager.get_config("logging")
    logging.basicConfig(
        level=getattr(logging, logging_config.level),
        format=logging_config.format,
    )

    logger.info("Bootstrapping application...")

    # Initialize database
    initialize_database()

    # Create default model client
    app_config = config_manager.get_config("app")
    model_client = create_default_client(app_config.default_model)

    # Create application manager
    app_manager = ApplicationManager(model_client=model_client)

    # Create application context
    context = ApplicationContext(
        config_manager=config_manager,
        app_manager=app_manager,
        model_client=model_client,
    )

    logger.info("Application bootstrapped successfully")

    return context
