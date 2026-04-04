from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.models import Agent, Run, Tenant
from agent_aichain.core.database import get_db
from agent_aichain.api.auth import get_current_user
from agent_aichain.models import User

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=dict)
async def create_agent(
    name: str = Body(...),
    role: str = Body(...),
    model: str = Body(...),
    description: Optional[str] = Body(None),
    instructions: Optional[str] = Body(None),
    tools: Optional[List[str]] = Body(None),
    config: Optional[dict] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent in the current tenant"""
    agent = Agent(
        name=name,
        role=role,
        model=model,
        description=description,
        instructions=instructions,
        tools=tools or [],
        config=config or {},
        tenant_id=current_user.tenant_id
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "model": agent.model,
        "tenant_id": agent.tenant_id
    }


@router.get("/", response_model=List[dict])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all agents for the current tenant"""
    result = await db.execute(
        select(Agent).where(Agent.tenant_id == current_user.tenant_id)
    )
    agents = result.scalars().all()

    return [
        {
            "id": a.id,
            "name": a.name,
            "role": a.role,
            "model": a.model,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in agents
    ]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific agent"""
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "role": agent.role,
        "model": agent.model,
        "config": agent.config,
        "tools": agent.tools,
        "instructions": agent.instructions,
        "is_active": agent.is_active,
        "created_at": agent.created_at.isoformat() if agent.created_at else None
    }


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an agent"""
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(agent)
    await db.commit()

    return {"message": "Agent deleted successfully"}