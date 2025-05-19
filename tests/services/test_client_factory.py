"""
Unit tests for the client factory service.
"""


import pytest
from agentic_fleet.services.client_factory import create_client, get_cached_client


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for Azure OpenAI."""
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-01")


def test_create_client_with_valid_env(mock_env_vars):
    """Test creating a client with valid environment variables."""
    # Directly use the mocked AzureOpenAIChatCompletionClient
    from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

    client = create_client(model_name="gpt-4o-mini-2024-07-18", streaming=True, vision=True)

    # Verify client is an instance of AzureOpenAIChatCompletionClient
    assert isinstance(client, AzureOpenAIChatCompletionClient)


def test_create_client_missing_env_vars(monkeypatch):
    """Test creating a client with missing environment variables."""
    # Remove all Azure OpenAI environment variables
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)

    # Expect a ValueError to be raised
    with pytest.raises(ValueError, match="Missing required Azure OpenAI environment variables"):
        create_client(model_name="gpt-4o-mini-2024-07-18", streaming=True, vision=True)


def test_get_cached_client(mock_env_vars):
    """Test that get_cached_client returns the same client for the same parameters."""
    # Create first client
    client1 = get_cached_client(model_name="gpt-4o-mini-2024-07-18", streaming=True, vision=True)

    # Create second client with same parameters
    client2 = get_cached_client(model_name="gpt-4o-mini-2024-07-18", streaming=True, vision=True)

    # Create client with different parameters
    client3 = get_cached_client(model_name="gpt-4o-mini-2024-07-18", streaming=False, vision=False)

    # Verify caching behavior
    assert client1 is client2  # Same parameters, should be the same client
    assert client1 is not client3  # Different parameters, should be different clients
