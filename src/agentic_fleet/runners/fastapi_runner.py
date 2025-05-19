"""FastAPI runner module for AgenticFleet."""

import logging
import os
import subprocess
from argparse import Namespace
from pathlib import Path

import uvicorn

from agentic_fleet.core.application.context import ApplicationContext

logger = logging.getLogger(__name__)


def run(app_context: ApplicationContext, args: Namespace) -> None:
    """Run the FastAPI server with Chainlit mounted.
    
    Args:
        app_context: Application context
        args: Command-line arguments
    """
    logger.info("Starting FastAPI server with Chainlit mounted")
    
    # Get API host and port from args or environment
    api_host = args.api_host or os.environ.get("API_HOST", "0.0.0.0")
    api_port = args.api_port or int(os.environ.get("API_PORT", "8080"))
    
    # Get Chainlit host and port from args or environment
    chainlit_host = args.chainlit_host or os.environ.get("CHAINLIT_HOST", "127.0.0.1")
    chainlit_port = args.chainlit_port or int(os.environ.get("CHAINLIT_PORT", "8000"))
    
    # Set environment variables for the FastAPI app
    os.environ["CHAINLIT_HOST"] = chainlit_host
    os.environ["CHAINLIT_PORT"] = str(chainlit_port)
    
    # Start the Chainlit server as a subprocess
    chainlit_app_path = Path(__file__).parent.parent / "chainlit_app.py"
    chainlit_cmd = [
        "chainlit", 
        "run", 
        str(chainlit_app_path), 
        "--host", 
        chainlit_host, 
        "--port", 
        str(chainlit_port),
        "--headless"  # Run without browser auto-open
    ]
    
    logger.info(f"Starting Chainlit server: {' '.join(chainlit_cmd)}")
    
    # Start the Chainlit server as a subprocess
    chainlit_process = subprocess.Popen(
        chainlit_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    logger.info(f"Chainlit server started with PID {chainlit_process.pid}")
    
    try:
        # Run the FastAPI server
        logger.info(f"Starting FastAPI server on {api_host}:{api_port}")
        uvicorn.run(
            "agentic_fleet.api.fastapi_app:app",
            host=api_host,
            port=api_port,
            reload=True,
        )
    finally:
        # Terminate the Chainlit server when the FastAPI server stops
        if chainlit_process.poll() is None:  # If process is still running
            logger.info(f"Terminating Chainlit server (PID {chainlit_process.pid})")
            chainlit_process.terminate()
            try:
                chainlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Chainlit server (PID {chainlit_process.pid}) did not terminate gracefully, killing it")
                chainlit_process.kill()
