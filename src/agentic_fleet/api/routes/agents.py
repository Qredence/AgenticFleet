"""
Routes for agent management.
"""


from fastapi import APIRouter, Depends, HTTPException

from agentic_fleet.api.dependencies.services import get_agent_service
from agentic_fleet.schemas.agent import Agent, AgentCreate, AgentUpdate
from agentic_fleet.services.agent_service import AgentService

# Create router
router = APIRouter()


@router.get("/", response_model=dict[str, list[Agent]])
async def list_agents(
    agent_service: AgentService = Depends(get_agent_service),
) -> dict[str, list[Agent]]:
    """
    List all available agents.
    """
    try:
        agents = await agent_service.list_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str, agent_service: AgentService = Depends(get_agent_service)
) -> Agent:
    """
    Get details for a specific agent.
    """
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Agent)
async def create_agent(
    agent: AgentCreate, agent_service: AgentService = Depends(get_agent_service)
) -> Agent:
    """
    Create a new agent.
    """
    try:
        return await agent_service.create_agent(agent)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str, agent: AgentUpdate, agent_service: AgentService = Depends(get_agent_service)
) -> Agent:
    """
    Update an existing agent.
    """
    try:
        updated_agent = await agent_service.update_agent(agent_id, agent)
        if not updated_agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return updated_agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}", response_model=dict[str, bool])
async def delete_agent(
    agent_id: str, agent_service: AgentService = Depends(get_agent_service)
) -> dict[str, bool]:
    """
    Delete an agent.
    """
    try:
        success = await agent_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
