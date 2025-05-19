#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

import click
from dotenv import load_dotenv


@click.group()
def cli():
    """AgenticFleet CLI"""
    pass


@cli.command()
@click.option("--port", default=8000, help="Port to run the application on")
def start(port):
    """Start AgenticFleet with OAuth enabled"""
    run_app(no_oauth=False, port=port)


@cli.command()
@click.option("--port", default=8000, help="Port to run the application on")
def no_oauth(port):
    """Start AgenticFleet without OAuth"""
    run_app(no_oauth=True, port=port)


def run_app(no_oauth: bool, port: int = 8000):
    # Load .env from project root
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    app_path = os.path.join(os.path.dirname(__file__), "..", "src", "agentic_fleet", "app.py")

    cmd = ["chainlit", "run", app_path, "--port", str(port)]

    if no_oauth:
        # Only disable OAuth-specific variables
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
        os.environ["DISABLE_OAUTH"] = "1"

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    cli()
