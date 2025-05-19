"""
Tests for the Agentic Fleet API.
"""


import pytest
from agentic_fleet.api.app import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """
    Test client fixture.
    """
    return TestClient(app)


def test_root_endpoint(client):
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data


def test_health_check(client):
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


class TestAgentsEndpoints:
    """
    Tests for the agents endpoints.
    """

    def test_list_agents(self, client):
        """
        Test listing agents.
        """
        response = client.get("/agents/")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_create_agent(self, client):
        """
        Test creating an agent.
        """
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent",
            "capabilities": ["text", "code"],
            "status": "active",
        }
        response = client.post("/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == agent_data["name"]
        assert data["description"] == agent_data["description"]

    def test_get_agent(self, client):
        """
        Test getting an agent.
        """
        # First create an agent
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent",
            "capabilities": ["text", "code"],
            "status": "active",
        }
        create_response = client.post("/agents/", json=agent_data)
        agent_id = create_response.json()["id"]

        # Then get the agent
        response = client.get(f"/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert data["name"] == agent_data["name"]


class TestTasksEndpoints:
    """
    Tests for the tasks endpoints.
    """

    def test_list_tasks(self, client):
        """
        Test listing tasks.
        """
        response = client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_create_task(self, client):
        """
        Test creating a task.
        """
        task_data = {"title": "Test Task", "description": "A test task", "status": "pending"}
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]


class TestChatEndpoints:
    """
    Tests for the chat endpoints.
    """

    def test_list_messages(self, client):
        """
        Test listing chat messages.
        """
        response = client.get("/chat/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_create_message(self, client):
        """
        Test creating a chat message.
        """
        message_data = {
            "content": "Hello, world!",
            "sender": "user",
            "receiver": "assistant",
            "session_id": "test_session",
        }
        response = client.post("/chat/messages", json=message_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["content"] == message_data["content"]
        assert data["sender"] == message_data["sender"]
