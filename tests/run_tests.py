#!/usr/bin/env python3
"""
Test runner script for Agentic Fleet.
This script runs all tests in the tests directory.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(args: argparse.Namespace) -> int:
    """Run the tests with the specified arguments."""
    # Base pytest command
    cmd: list[str] = ["pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add test directory
    cmd.append(str(Path(__file__).parent))

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=src.agentic_fleet", "--cov-report=term-missing", "--cov-report=xml"])

    # Add any additional arguments
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    # Run the tests
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Agentic Fleet tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("pytest_args", nargs="*", help="Additional pytest arguments")

    args = parser.parse_args()
    sys.exit(run_tests(args))
