"""Tests for the client factory module."""

from unittest.mock import patch

import pytest
from agentic_fleet.services.client_factory import create_client, get_cached_client


def test_create_client(mock_env_vars, mock_openai_client):
    """Test creating a client with specific parameters."""
    client = create_client(model_name="gpt-4o-mini-2024-07-18", streaming=True, vision=True)

    assert client is mock_openai_client
    assert client.model == "gpt-4o-mini-2024-07-18"
    assert client.model_info["vision"] is True


def test_cached_client_same_params(mock_env_vars, mock_openai_client):
    """Test that clients with the same parameters are cached."""
    # Clear the LRU cache to ensure consistent test behavior
    get_cached_client.cache_clear()

    client1 = get_cached_client(model_name="gpt-4o-mini-2024-07-18")
    client2 = get_cached_client(model_name="gpt-4o-mini-2024-07-18")

    assert client1 is client2
    assert client1 is mock_openai_client


def test_missing_env_vars():
    """Test error handling when environment variables are missing."""
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(ValueError, match="Missing required Azure OpenAI environment variables"),
    ):
        create_client(model_name="gpt-4o-mini-2024-07-18")


def test_model_family_detection(mock_env_vars, mock_openai_client):
    """Test model family detection based on model name."""
    # Test GPT-4o model family
    client1 = create_client(model_name="gpt-4o-mini-2024-07-18")

    # Use a different mock for a non-GPT-4o model
    with patch(
        "agentic_fleet.services.client_factory.AzureOpenAIChatCompletionClient"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.model = "gpt-35-turbo"
        mock_client.model_info = {"family": "azure", "vision": False}

        # Test Azure model family
        client2 = create_client(model_name="gpt-35-turbo")

        assert mock_client_class.call_args[1]["model_info"]["family"] == "azure"


def test_cached_client_different_params(mock_env_vars):
    client1 = get_cached_client(model_name="gpt-4o-mini-2024-07-18", vision=True)
    client2 = get_cached_client(model_name="gpt-4o-mini-2024-07-18", vision=False)

    assert client1 is not client2
