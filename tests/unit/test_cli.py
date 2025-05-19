"""Unit tests for CLI module."""

import os
from unittest.mock import patch

from agentic_fleet.cli import cli
from click.testing import CliRunner


def test_get_app_path():
    """Test get_app_path returns correct path."""
    app_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "src",
        "agentic_fleet",
        "app.py",
    )
    assert os.path.exists(app_path)
    assert app_path.endswith("app.py")


def test_get_config_path_default():
    """Test get_config_path with default OAuth setting."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "config.oauth.toml"
    )
    assert config_path.endswith("config.oauth.toml")


def test_get_config_path_no_oauth():
    """Test get_config_path with OAuth disabled."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "config.no-oauth.toml",
    )
    assert config_path.endswith("config.no-oauth.toml")


def test_cli_start_default():
    """Test CLI start command with default settings."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(cli, ["start"])
        assert result.exit_code == 0
        assert "Starting AgenticFleet with OAuth..." in result.output
        mock_run.assert_called_once()


def test_cli_start_no_oauth():
    """Test CLI start command with OAuth disabled."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(cli, ["start", "no-oauth"])
        assert result.exit_code == 0
        assert "Starting AgenticFleet without OAuth..." in result.output
        mock_run.assert_called_once()


def test_cli_start_invalid_mode():
    """Test CLI start command with invalid mode."""
    runner = CliRunner()
    result = runner.invoke(cli, ["start", "invalid"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '[[default|no-oauth]]': 'invalid' is not one of 'default', 'no-oauth'"
        in result.output
    )
