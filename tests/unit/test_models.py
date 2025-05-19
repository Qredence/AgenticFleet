"""Unit tests for the models module."""

from unittest.mock import AsyncMock, Mock

import pytest
from agentic_fleet.models.models import EnhancedAssistantAgent, create_agent_team
from autogen_core.models import ChatCompletionClient


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    client = Mock(spec=ChatCompletionClient)
    client.generate = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_enhanced_assistant_agent_initialization(mock_model_client):
    """Test initialization of EnhancedAssistantAgent."""
    agent = EnhancedAssistantAgent(
        name="test_agent", system_message="test message", model_client=mock_model_client
    )
    assert agent is not None
    assert agent.name == "test_agent"


@pytest.mark.asyncio
async def test_enhanced_assistant_agent_process_message(mock_model_client):
    """Test message processing in EnhancedAssistantAgent."""
    agent = EnhancedAssistantAgent(
        name="test_agent", system_message="test message", model_client=mock_model_client
    )

    mock_model_client.generate.return_value = "test response"

    result = await agent.process_message("test message")
    assert result is not None
    assert result.chat_message.content == "test response"


@pytest.mark.asyncio
async def test_enhanced_assistant_agent_error_handling(mock_model_client):
    """Test error handling in EnhancedAssistantAgent."""
    agent = EnhancedAssistantAgent(
        name="test_agent", system_message="test message", model_client=mock_model_client
    )

    mock_model_client.generate.side_effect = Exception("test error")

    result = await agent.process_message("test message")
    assert result is not None
    assert result.chat_message.content == "Error processing message: test error"


@pytest.mark.asyncio
async def test_create_agent_team():
    """Test creation of agent team."""
    agent1 = EnhancedAssistantAgent(name="agent1", system_message="test message 1")
    agent2 = EnhancedAssistantAgent(name="agent2", system_message="test message 2")
    agents = [agent1, agent2]
    team_config = {"max_rounds": 5, "temperature": 0.7}

    result = await create_agent_team(agents, team_config)
    assert result is not None
    assert len(result) == 2
    assert all(isinstance(agent, EnhancedAssistantAgent) for agent in result)
