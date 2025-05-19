"""Tests for the settings handler module."""

from unittest.mock import MagicMock

import pytest
from agentic_fleet.ui.settings_handler import SettingsManager, chat_profiles


def test_default_settings():
    """Test default settings have expected keys and valid values."""
    settings_manager = SettingsManager()
    default_settings = settings_manager.get_default_settings()

    # Check that default settings contain expected keys
    assert "temperature" in default_settings
    assert "max_rounds" in default_settings

    # Check that temperature is a float between 0 and 1
    assert isinstance(default_settings["temperature"], float)
    assert 0 <= default_settings["temperature"] <= 1

    # Check that max_rounds is an integer
    assert isinstance(default_settings["max_rounds"], int)


@pytest.mark.asyncio
async def test_setup_chat_settings(mock_settings_components):
    """Test setting up chat settings."""
    settings_manager = SettingsManager()

    # Mock get_default_settings to return specific settings
    settings_manager.get_default_settings = MagicMock(
        return_value={
            "temperature": 0.7,
            "max_rounds": 10,
            "max_time": 600,
            "max_stalls": 3,
            "start_page": "agents",
            "system_prompt": "Default prompt",
        }
    )

    await settings_manager.setup_chat_settings()

    # Check that ChatSettings was created
    assert mock_settings_components["ChatSettings"].called

    # Check that each setting component was created
    assert mock_settings_components["Select"].call_count >= 1
    assert mock_settings_components["Slider"].call_count >= 1


@pytest.mark.asyncio
async def test_handle_settings_update(mock_user_session, mock_settings_components):
    """Test handling settings updates."""
    settings_manager = SettingsManager()

    # Create mock settings
    mock_settings = {"temperature": 0.8, "max_rounds": 15}

    # Store initial settings in mock session
    mock_user_session["settings"] = {"temperature": 0.7, "max_rounds": 10}

    await settings_manager.handle_settings_update(mock_settings)

    # Check that settings were updated in user session
    assert mock_user_session["settings"]["temperature"] == 0.8
    assert mock_user_session["settings"]["max_rounds"] == 15


def test_chat_profiles():
    """Test that chat profiles are created with required attributes."""
    # Since chat_profiles is no longer async, we can call it directly
    profiles = chat_profiles()

    # Check that profiles is a non-empty list
    assert profiles
    assert isinstance(profiles, list)

    # Check that each profile has required attributes
    for profile in profiles:
        assert hasattr(profile, "id")
        assert hasattr(profile, "name")
        assert profile.id
        assert profile.name

        # All profiles should have settings and icon attributes
        assert hasattr(profile, "settings")
        assert hasattr(profile, "icon")


@pytest.mark.asyncio
async def test_chat_settings_combined_flow(mock_user_session, mock_settings_components):
    """Test a combined flow of setting up and updating chat settings."""
    settings_manager = SettingsManager()

    # Mock get_default_settings to return specific settings
    settings_manager.get_default_settings = MagicMock(
        return_value={"temperature": 0.7, "max_rounds": 10}
    )

    # 1. Set up chat settings
    await settings_manager.setup_chat_settings()

    # 2. Update settings
    new_settings = {"temperature": 0.9}
    await settings_manager.handle_settings_update(new_settings)

    # 3. Check the combined result
    assert mock_user_session["settings"]["temperature"] == 0.9
    assert mock_user_session["settings"]["max_rounds"] == 10  # Unchanged
