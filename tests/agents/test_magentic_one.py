"""
Unit tests for the MagenticOne agent implementation.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# from agentic_fleet.core.agents.magentic_one import MagenticOneAgent, create_magentic_one_agent
# TEST SKIPPED: MagenticOneAgent no longer exists in the codebase.


@pytest.fixture
def mock_client():
    """Create a mock client with the required model_info attribute."""
    mock_client = AsyncMock()
    mock_client.model_info = {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "family": "gpt-4o",
        "architecture": "gpt-4o-mini-2024-07-18",
    }
    return mock_client


@pytest.fixture
def mock_code_executor():
    """Create a mock code executor for testing."""
    return Mock()


@pytest.fixture
def mock_web_surfer():
    """Mock the WebSurfer initialization."""
    with patch(
        "autogen_ext.agents.web_surfer._multimodal_web_surfer.MultimodalWebSurfer", autospec=True
    ) as mock_web_surfer:
        yield mock_web_surfer


@pytest.fixture
def mock_magentic_one_team():
    """Mock the AutogenMagenticOne team."""
    mock_team = AsyncMock()
    mock_team.run.return_value = "Task completed"

    async def mock_run_stream(task):
        chunks = ["Response chunk 1", "Response chunk 2"]
        for chunk in chunks:
            yield chunk

    mock_team.run_stream.side_effect = mock_run_stream
    return mock_team


@pytest.fixture
def mock_chainlit_context():
    """Mock the Chainlit context."""
    return Mock()


@pytest.mark.asyncio
async def test_magentic_one_agent_initialization(
    mock_client, mock_code_executor, mock_web_surfer, mock_magentic_one_team, mock_chainlit_context
):
    """Test the initialization of the MagenticOne agent."""
    # Patch the AutogenMagenticOne initialization to avoid context issues
    with patch(
        "autogen_ext.teams.magentic_one.MagenticOneGroupChat", return_value=mock_magentic_one_team
    ):
        agent = MagenticOneAgent(
            client=mock_client, code_executor=mock_code_executor, hil_mode=True
        )

        assert agent.client == mock_client
        assert agent.code_executor == mock_code_executor
        assert agent.hil_mode is True
        assert agent.agent is not None


@pytest.mark.asyncio
async def test_create_magentic_one_agent(
    mock_client, mock_code_executor, mock_web_surfer, mock_magentic_one_team, mock_chainlit_context
):
    """Test the create_magentic_one_agent factory function."""
    # Patch the AutogenMagenticOne initialization to avoid context issues
    with patch(
        "autogen_ext.teams.magentic_one.MagenticOneGroupChat", return_value=mock_magentic_one_team
    ):
        agent = create_magentic_one_agent(
            client=mock_client, code_executor=mock_code_executor, hil_mode=False
        )

        assert isinstance(agent, MagenticOneAgent)
        assert agent.client == mock_client
        assert agent.code_executor == mock_code_executor
        assert agent.hil_mode is False


@pytest.mark.asyncio
async def test_magentic_one_agent_run_stream(
    mock_client, mock_code_executor, mock_web_surfer, mock_magentic_one_team, mock_chainlit_context
):
    """Test the run_stream method of the MagenticOne agent."""
    # Patch the AutogenMagenticOne initialization to avoid context issues
    with patch(
        "autogen_ext.teams.magentic_one.MagenticOneGroupChat", return_value=mock_magentic_one_team
    ):
        # Create our MagenticOneAgent
        agent = MagenticOneAgent(
            client=mock_client, code_executor=mock_code_executor, hil_mode=True
        )

        # Test run_stream
        task = "Test task"
        stream_iterator = agent.run_stream(task)

        results = []
        async for chunk in stream_iterator:
            results.append(chunk)

        # Verify
        mock_magentic_one_team.run_stream.assert_called_once_with(task=task)
        assert results == ["Response chunk 1", "Response chunk 2"]


@pytest.mark.asyncio
async def test_magentic_one_agent_run(
    mock_client, mock_code_executor, mock_web_surfer, mock_magentic_one_team, mock_chainlit_context
):
    """Test the run method of the MagenticOne agent."""
    # Patch the AutogenMagenticOne initialization to avoid context issues
    with patch(
        "autogen_ext.teams.magentic_one.MagenticOneGroupChat", return_value=mock_magentic_one_team
    ):
        # Create our MagenticOneAgent
        agent = MagenticOneAgent(
            client=mock_client, code_executor=mock_code_executor, hil_mode=True
        )

        # Test run
        task = "Test task"
        result = await agent.run(task)

        # Verify
        mock_magentic_one_team.run.assert_called_once_with(task=task)
        assert result == "Task completed"
