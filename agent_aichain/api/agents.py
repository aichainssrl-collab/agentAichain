from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.models import Agent, Run, Tenant, AIModel
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
    # Validate model exists and is active
    result = await db.execute(
        select(AIModel).where(
            AIModel.name == model,
            AIModel.is_active == True
        )
    )
    ai_model = result.scalar_one_or_none()
    if ai_model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model}' not found or is inactive. Please select an active model from Settings."
        )

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


@router.put("/{agent_id}")
async def update_agent(
    agent_id: int,
    name: Optional[str] = Body(None),
    role: Optional[str] = Body(None),
    model: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    instructions: Optional[str] = Body(None),
    tools: Optional[List[str]] = Body(None),
    config: Optional[dict] = Body(None),
    is_active: Optional[bool] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing agent"""
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # If model is being updated, validate it exists and is active
    if model is not None:
        result = await db.execute(
            select(AIModel).where(
                AIModel.name == model,
                AIModel.is_active == True
            )
        )
        ai_model = result.scalar_one_or_none()
        if ai_model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' not found or is inactive. Please select an active model from Settings."
            )

    # Update fields if provided
    if name is not None:
        agent.name = name
    if role is not None:
        agent.role = role
    if model is not None:
        agent.model = model
    if description is not None:
        agent.description = description
    if instructions is not None:
        agent.instructions = instructions
    if tools is not None:
        agent.tools = tools
    if config is not None:
        agent.config = config
    if is_active is not None:
        agent.is_active = is_active

    await db.commit()
    await db.refresh(agent)

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
        "tenant_id": agent.tenant_id
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