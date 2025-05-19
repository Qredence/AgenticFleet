"""Main entry point for AgenticFleet.

This module provides a unified entry point for all application modes:
- chainlit: Run the Chainlit UI
- api: Run the API server
- fastapi: Run the FastAPI server with Chainlit mounted
"""

import argparse
import logging
import sys

from agentic_fleet.core.bootstrap import bootstrap_application
from agentic_fleet.runners import api_runner, chainlit_runner, fastapi_runner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agentic_fleet")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="AgenticFleet - Multi-agent AI system")

    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="mode", help="Mode to run the application in")

    # Chainlit mode
    chainlit_parser = subparsers.add_parser("chainlit", help="Run the Chainlit UI")
    chainlit_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    chainlit_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    chainlit_parser.add_argument(
        "--no-oauth", action="store_true", help="Disable OAuth authentication"
    )

    # API mode
    api_parser = subparsers.add_parser("api", help="Run the API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # FastAPI mode
    fastapi_parser = subparsers.add_parser(
        "fastapi", help="Run the FastAPI server with Chainlit mounted"
    )
    fastapi_parser.add_argument("--api-host", default="0.0.0.0", help="Host for the API server")
    fastapi_parser.add_argument(
        "--api-port", type=int, default=8080, help="Port for the API server"
    )
    fastapi_parser.add_argument(
        "--chainlit-host", default="127.0.0.1", help="Host for the Chainlit server"
    )
    fastapi_parser.add_argument(
        "--chainlit-port", type=int, default=8000, help="Port for the Chainlit server"
    )

    # Parse arguments
    args = parser.parse_args()

    # Set default mode if none specified
    if not args.mode:
        logger.info("No mode specified, defaulting to 'chainlit'")
        args.mode = "chainlit"
        # Create default args for chainlit mode
        args.host = "0.0.0.0"
        args.port = 8000
        args.no_oauth = False

    # Bootstrap the application
    logger.info(f"Bootstrapping application in {args.mode} mode")
    app_context = bootstrap_application()

    # Run the application in the specified mode
    if args.mode == "chainlit":
        chainlit_runner.run(app_context, args)
    elif args.mode == "api":
        api_runner.run(app_context, args)
    elif args.mode == "fastapi":
        fastapi_runner.run(app_context, args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
