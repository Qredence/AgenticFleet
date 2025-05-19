"""Chainlit runner module for AgenticFleet."""

import logging
import os
import subprocess
from argparse import Namespace
from pathlib import Path

from agentic_fleet.core.application.context import ApplicationContext

logger = logging.getLogger(__name__)


def run(app_context: ApplicationContext, args: Namespace) -> None:
    """Run the Chainlit app.
    
    Args:
        app_context: Application context
        args: Command-line arguments
    """
    logger.info("Starting Chainlit app")
    
    # Store application context in environment for Chainlit app to access
    os.environ["AGENTIC_FLEET_APP_CONTEXT"] = "1"
    
    # Get host and port from args or environment
    host = args.host or os.environ.get("CHAINLIT_HOST", "0.0.0.0")
    port = args.port or int(os.environ.get("CHAINLIT_PORT", "8000"))
    
    # Set OAuth flag
    if args.no_oauth:
        os.environ["DISABLE_OAUTH"] = "1"
        # Remove OAuth-specific environment variables
        oauth_vars = [
            "OAUTH_GITHUB_CLIENT_ID",
            "OAUTH_GITHUB_CLIENT_SECRET",
            "OAUTH_PROMPT",
            "OAUTH_GITHUB_PROMPT",
            "OAUTH_USER_PROMPT",
        ]
        for var in oauth_vars:
            if var in os.environ:
                del os.environ[var]
    
    # Get the path to the chainlit_app.py file
    app_path = Path(__file__).parent.parent / "chainlit_app.py"
    
    # Build the command to run the Chainlit app
    cmd = [
        "chainlit", 
        "run", 
        str(app_path), 
        "--host", 
        host, 
        "--port", 
        str(port)
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Run the Chainlit app
    subprocess.run(cmd, check=True)
