"""
Service for agent management.
"""

import logging
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from agentic_fleet.database.models.agent import Agent as AgentModel
from agentic_fleet.database.session import get_db
from agentic_fleet.schemas.agent import Agent, AgentCreate, AgentUpdate

# Initialize logging
logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agents."""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        """
        Initialize the agent service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_agent(self, agent: AgentCreate) -> Agent:
        """
        Create a new agent.

        Args:
            agent: The agent data to create

        Returns:
            The created agent
        """
        try:
            # Create a new agent model
            agent_model = AgentModel(
                name=agent.name,
                description=agent.description,
                model=agent.model,
                provider=agent.parameters.get("provider", "openai"),
                system_prompt=agent.parameters.get("system_prompt", ""),
            )

            # Add to database
            self.db.add(agent_model)
            await self.db.commit()
            await self.db.refresh(agent_model)

            # Convert to schema
            return Agent(
                id=str(agent_model.id),
                name=agent_model.name,
                description=agent_model.description,
                capabilities=[],  # Add capabilities mapping if needed
                model=agent_model.model,
                parameters={
                    "provider": agent_model.provider,
                    "system_prompt": agent_model.system_prompt,
                },
                created_at=agent_model.created_at,
                updated_at=agent_model.updated_at,
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating agent: {str(e)}")
            raise

    async def get_agent(self, agent_id: str) -> Agent | None:
        """
        Get an agent by ID.

        Args:
            agent_id: The ID of the agent to retrieve

        Returns:
            The agent if found, None otherwise
        """
        try:
            # Query the database
            result = await self.db.execute(select(AgentModel).where(AgentModel.id == agent_id))
            agent_model = result.scalars().first()

            if not agent_model:
                return None

            # Convert to schema
            return Agent(
                id=str(agent_model.id),
                name=agent_model.name,
                description=agent_model.description,
                capabilities=[],  # Add capabilities mapping if needed
                model=agent_model.model,
                parameters={
                    "provider": agent_model.provider,
                    "system_prompt": agent_model.system_prompt,
                },
                created_at=agent_model.created_at,
                updated_at=agent_model.updated_at,
            )
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            raise

    async def update_agent(self, agent_id: str, agent: AgentUpdate) -> Agent | None:
        """
        Update an existing agent.

        Args:
            agent_id: The ID of the agent to update
            agent: The updated agent data

        Returns:
            The updated agent if found, None otherwise
        """
        try:
            # Check if agent exists
            result = await self.db.execute(select(AgentModel).where(AgentModel.id == agent_id))
            agent_model = result.scalars().first()

            if not agent_model:
                return None

            # Update fields
            update_data = agent.dict(exclude_unset=True)

            # Handle nested parameters
            if "parameters" in update_data:
                parameters = update_data.pop("parameters", {})
                if "provider" in parameters:
                    agent_model.provider = parameters["provider"]
                if "system_prompt" in parameters:
                    agent_model.system_prompt = parameters["system_prompt"]

            # Update direct fields
            for key, value in update_data.items():
                if hasattr(agent_model, key) and value is not None:
                    setattr(agent_model, key, value)

            # Update timestamp
            agent_model.updated_at = datetime.utcnow()

            # Commit changes
            await self.db.commit()
            await self.db.refresh(agent_model)

            # Convert to schema
            return Agent(
                id=str(agent_model.id),
                name=agent_model.name,
                description=agent_model.description,
                capabilities=[],  # Add capabilities mapping if needed
                model=agent_model.model,
                parameters={
                    "provider": agent_model.provider,
                    "system_prompt": agent_model.system_prompt,
                },
                created_at=agent_model.created_at,
                updated_at=agent_model.updated_at,
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating agent {agent_id}: {str(e)}")
            raise

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: The ID of the agent to delete

        Returns:
            True if the agent was deleted, False otherwise
        """
        try:
            # Check if agent exists
            result = await self.db.execute(select(AgentModel).where(AgentModel.id == agent_id))
            agent_model = result.scalars().first()

            if not agent_model:
                return False

            # Delete the agent
            await self.db.delete(agent_model)
            await self.db.commit()

            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting agent {agent_id}: {str(e)}")
            raise

    async def list_agents(self) -> list[Agent]:
        """
        List all agents.

        Returns:
            A list of all agents
        """
        try:
            # Query all agents
            result = await self.db.execute(select(AgentModel))
            agent_models = result.scalars().all()

            # Convert to schemas
            return [
                Agent(
                    id=str(agent_model.id),
                    name=agent_model.name,
                    description=agent_model.description,
                    capabilities=[],  # Add capabilities mapping if needed
                    model=agent_model.model,
                    parameters={
                        "provider": agent_model.provider,
                        "system_prompt": agent_model.system_prompt,
                    },
                    created_at=agent_model.created_at,
                    updated_at=agent_model.updated_at,
                )
                for agent_model in agent_models
            ]
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise
