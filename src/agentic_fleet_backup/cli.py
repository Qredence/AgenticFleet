"""Command line interface for AgenticFleet."""

import os
import subprocess
import sys
from typing import Optional

import click
from dotenv import load_dotenv

from agentic_fleet.config import config_manager


def validate_environment() -> Optional[str]:
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
    # Initialize configuration
    config_manager.load_all()


@cli.command()
@click.argument('mode', type=click.Choice(['default', 'no-oauth']), default='default')
@click.option('--host', default=None, help='Host to bind to')
@click.option('--port', default=None, type=int, help='Port to bind to')
def start(mode: str, host: Optional[str], port: Optional[int]):
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

        # Get application settings
        app_settings = config_manager.get_app_settings()
        security_settings = config_manager.get_security_settings()

        # Set OAuth environment variables based on mode
        if mode == 'no-oauth':
            os.environ["USE_OAUTH"] = "false"
            os.environ["OAUTH_CLIENT_ID"] = ""
            os.environ["OAUTH_CLIENT_SECRET"] = ""
            click.echo("Starting AgenticFleet without OAuth...")
        else:
            os.environ["USE_OAUTH"] = str(security_settings.get("use_oauth", "false")).lower()
            click.echo("Starting AgenticFleet with OAuth...")

        # Get the path to app.py
        app_dir = os.path.abspath(os.path.dirname(__file__))
        app_path = os.path.join(app_dir, "app.py")

        # Set host and port
        if host:
            os.environ["HOST"] = host
        if port:
            os.environ["PORT"] = str(port)

        # Run chainlit with the configured app
        cmd = ["chainlit", "run", app_path]
        
        # Add host if specified
        if host:
            cmd.extend(["--host", host])
        
        # Add port if specified
        if port:
            cmd.extend(["--port", str(port)])

        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        click.echo(f"Error running chainlit: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error starting AgenticFleet: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Display AgenticFleet version information."""
    from agentic_fleet import __version__
    click.echo(f"AgenticFleet version {__version__}")


@cli.command()
def config():
    """Display current configuration."""
    click.echo("\nAgenticFleet Configuration:")
    click.echo("-" * 50)

    # Display app settings
    app_settings = config_manager.get_app_settings()
    click.echo("\nApplication Settings:")
    click.echo(f"  Name: {app_settings['app']['name']}")
    click.echo(f"  Version: {app_settings['app']['version']}")
    click.echo(f"  Host: {app_settings['app'].get('host', 'localhost')}")
    click.echo(f"  Port: {app_settings['app'].get('port', 8001)}")

    # Display environment settings
    env_settings = config_manager.get_environment_settings()
    click.echo("\nEnvironment Settings:")
    click.echo(f"  Debug Mode: {env_settings.get('debug', False)}")
    click.echo(f"  Workspace: {env_settings.get('workspace_dir', './files/workspace')}")
    click.echo(f"  Downloads: {env_settings.get('downloads_dir', './files/downloads')}")

    # Display model settings
    model_settings = config_manager.get_model_settings("azure")
    click.echo("\nModel Settings:")
    click.echo(f"  Provider: Azure OpenAI")
    click.echo(f"  API Version: {model_settings.get('config', {}).get('api_version', 'Not set')}")
    click.echo("  Available Models:")
    for model in model_settings.get("models", {}).keys():
        click.echo(f"    - {model}")

    click.echo("\n" + "-" * 50)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
