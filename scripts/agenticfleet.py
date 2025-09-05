#!/usr/bin/env python3
"""Entry point script for AgenticFleet."""

import os
import subprocess
import sys

# Add src directory to path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, src_dir)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: agenticfleet <command>")
        print("Commands:")
        print("  start         Start with OAuth enabled")
        print("  start no-oauth  Start without OAuth")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        # Check for no-oauth flag
        no_oauth = len(sys.argv) > 2 and sys.argv[2] == "no-oauth"
        if not no_oauth:
            print("Starting AgenticFleet with OAuth...")
        else:
            print("Starting AgenticFleet without OAuth...")
            os.environ["USE_OAUTH"] = "false"

        # Get the path to app.py
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "agentic_fleet"))
        app_path = os.path.join(app_dir, "app.py")

        # Build chainlit command
        cmd = ["chainlit", "run", app_path, "--port", "8000"]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running chainlit: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
