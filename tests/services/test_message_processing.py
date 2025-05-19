"""
Unit tests for the message processing service.
"""

import pytest
from agentic_fleet.services.message_processing import process_response
from autogen_agentchat.messages import TextMessage


@pytest.mark.asyncio
async def test_process_response_text_message(mock_chainlit_context):
    """Test processing a TextMessage response."""
    # Create a mock TextMessage
    mock_message = TextMessage(content="Test response message", source="TestAgent")

    response_text, plan_update = await process_response(mock_message)

    # Verify response processing
    assert response_text == "Test response message"
    assert plan_update is None


@pytest.mark.asyncio
async def test_process_response_with_plan(mock_chainlit_context):
    """Test processing a response with a plan."""
    # Create a TextMessage with a plan
    mock_message = TextMessage(
        content=(
            "Here is the task overview.\n\n"
            "Here is the plan to follow as best as possible:\n"
            "1. First step\n"
            "2. Second step"
        ),
        source="PlanningAgent",
    )

    response_text, plan_update = await process_response(mock_message)

    # Verify response processing
    assert "Here is the task overview" in response_text
    assert plan_update == "1. First step\n2. Second step"


@pytest.mark.asyncio
async def test_process_response_list(mock_chainlit_context):
    """Test processing a list of responses."""
    # Create a list of TextMessages
    mock_messages = [
        TextMessage(content="First message", source="Agent1"),
        TextMessage(content="Second message", source="Agent2"),
    ]

    response_text, plan_update = await process_response(mock_messages)

    # Verify response processing
    assert response_text == "Second message"
    assert plan_update is None


@pytest.mark.asyncio
async def test_process_response_dict(mock_chainlit_context):
    """Test processing a dictionary response."""
    # Create a dictionary response
    mock_dict_response = {"content": "Dictionary response message"}

    response_text, plan_update = await process_response(mock_dict_response)

    # Verify response processing
    assert response_text == "Dictionary response message"
    assert plan_update is None


@pytest.mark.asyncio
async def test_process_response_error_handling(mock_chainlit_context):
    """Test error handling in response processing."""
    # Create an invalid response type
    invalid_response = 42

    response_text, plan_update = await process_response(invalid_response)

    # Verify response processing
    assert response_text == "42"
    assert plan_update is None
