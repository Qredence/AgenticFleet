"""Command line interface for AgenticFleet."""

import os
import subprocess
import sys

import click
from dotenv import load_dotenv

from agentic_fleet.config import config_manager
from agentic_fleet.core.application import bootstrap


def validate_environment() -> str | None:
    """Validate required environment variables.

    Returns:
        Error message if validation fails, None otherwise
    """
    if error := config_manager.validate_environment():
        return error
    return None


@click.group()
def cli():
    """AgenticFleet CLI - A multi-agent system for adaptive AI reasoning."""
    pass


@cli.command()
@click.argument("mode", type=click.Choice(["default", "no-oauth"]), default="default")
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
def start(mode: str, host: str | None, port: int | None):
    """Start AgenticFleet with specified configuration.

    Args:
        mode: Operating mode ('default' or 'no-oauth')
        host: Optional host to bind to
        port: Optional port to bind to
    """
    try:
        # Load environment variables
        load_dotenv()

        # Validate environment
        if error := validate_environment():
            click.echo(f"Environment validation failed: {error}", err=True)
            sys.exit(1)

        # Set OAuth environment variables based on mode
        if mode == "no-oauth":
            os.environ["USE_OAUTH"] = "false"
            os.environ["OAUTH_CLIENT_ID"] = ""
            os.environ["OAUTH_CLIENT_SECRET"] = ""

        # Initialize application through bootstrap
        app = bootstrap.initialize_app()

        # Get host and port from environment or CLI args
        final_host = host or app.config.host
        final_port = port or app.config.port

        # Start Chainlit server
        command = [
            "chainlit",
            "run",
            "src/agentic_fleet/app.py",
            "--host",
            final_host,
            "--port",
            str(final_port),
            "--headless",  # Run without browser auto-open
        ]

        click.echo(f"Starting AgenticFleet on {final_host}:{final_port}")
        subprocess.run(command, check=True)

    except Exception as e:
        click.echo(f"Error starting AgenticFleet: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Display AgenticFleet version information."""
    try:
        from agentic_fleet import __version__

        click.echo(f"AgenticFleet version: {__version__}")
    except ImportError:
        click.echo("Could not determine version", err=True)
        sys.exit(1)


@cli.command()
def config():
    """Display current configuration."""
    try:
        app = bootstrap.initialize_app()
        click.echo("\nApplication Configuration:")
        click.echo("-" * 30)
        for key, value in app.config.settings.items():
            click.echo(f"{key}: {value}")
    except Exception as e:
        click.echo(f"Error displaying configuration: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
