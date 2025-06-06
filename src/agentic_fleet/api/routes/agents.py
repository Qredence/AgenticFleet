"""
Routes for agent management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from agentic_fleet.api.dependencies.services import get_agent_service
from agentic_fleet.schemas.agent import Agent, AgentCreate, AgentUpdate
from agentic_fleet.services.agent_service import AgentService

# Create router
router = APIRouter()


@router.get("/", response_model=Dict[str, List[Agent]])
async def list_agents(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, List[Agent]]:
    """
    List all available agents.
    
    Returns a list of all agents in the system with their current status,
    capabilities, and configuration details.
    
    Note: Future versions may support query parameters for filtering by status,
    capabilities, or pagination (limit, offset).
    
    Returns:
        Dict containing a list of all agents
    """
    try:
        agents = await agent_service.list_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, agent_service: AgentService = Depends(get_agent_service)) -> Agent:
    """
    Get details for a specific agent.
    
    Retrieves detailed information about a specific agent including its
    configuration, current status, and capabilities.
    
    Args:
        agent_id: The unique identifier of the agent
        
    Returns:
        Agent object with detailed information
        
    Raises:
        HTTPException: 404 if agent not found
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
async def create_agent(agent: AgentCreate, agent_service: AgentService = Depends(get_agent_service)) -> Agent:
    """
    Create a new agent.
    
    Creates a new AI agent with the specified configuration and capabilities.
    The agent will be available for task assignment once created.
    
    Args:
        agent: Agent creation data including name, type, and configuration
        
    Returns:
        The created agent with assigned ID and status
        
    Raises:
        HTTPException: 500 if creation fails
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
    
    Updates the configuration, capabilities, or status of an existing agent.
    Only provided fields will be updated; others remain unchanged.
    
    Args:
        agent_id: The unique identifier of the agent to update
        agent: Agent update data with fields to modify
        
    Returns:
        The updated agent with new configuration
        
    Raises:
        HTTPException: 404 if agent not found, 500 if update fails
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


@router.delete("/{agent_id}", response_model=Dict[str, bool])
async def delete_agent(agent_id: str, agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, bool]:
    """
    Delete an agent.
    
    Permanently removes an agent from the system. This action cannot be undone.
    Any tasks assigned to this agent will need to be reassigned.
    
    Args:
        agent_id: The unique identifier of the agent to delete
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: 404 if agent not found, 500 if deletion fails
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
