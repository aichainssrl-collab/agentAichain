from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from agent_aichain.models import Team, Agent, Tenant, team_agents
from agent_aichain.core.database import get_db
from agent_aichain.api.auth import get_current_user
from agent_aichain.models import User

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/", response_model=dict)
async def create_team(
    name: str = Body(...),
    mode: Optional[str] = Body("coordinate"),
    max_iterations: Optional[int] = Body(10),
    config: Optional[dict] = Body(None),
    agent_ids: Optional[List[int]] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new team in the current tenant"""
    team = Team(
        name=name,
        mode=mode,
        max_iterations=max_iterations,
        config=config or {},
        tenant_id=current_user.tenant_id
    )
    db.add(team)
    await db.flush()

    # Add agents to team if provided
    if agent_ids:
        result = await db.execute(
            select(Agent).where(
                Agent.id.in_(agent_ids),
                Agent.tenant_id == current_user.tenant_id
            )
        )
        agents = result.scalars().all()

        if len(agents) != len(agent_ids):
            raise HTTPException(status_code=400, detail="Some agents not found or not in tenant")

        team.agents = agents

    await db.commit()
    await db.refresh(team)

    return {
        "id": team.id,
        "name": team.name,
        "mode": team.mode,
        "tenant_id": team.tenant_id,
        "agent_count": len(team.agents)
    }


@router.get("/", response_model=List[dict])
async def list_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all teams for the current tenant"""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents))
        .where(Team.tenant_id == current_user.tenant_id)
    )
    teams = result.scalars().all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "mode": t.mode,
            "agent_count": len(t.agents),
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in teams
    ]


@router.get("/{team_id}")
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific team with its agents"""
    result = await db.execute(
        select(Team).where(
            Team.id == team_id,
            Team.tenant_id == current_user.tenant_id
        )
    )
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "mode": team.mode,
        "max_iterations": team.max_iterations,
        "config": team.config,
        "agents": [
            {"id": a.id, "name": a.name, "role": a.role}
            for a in team.agents
        ],
        "created_at": team.created_at.isoformat() if team.created_at else None
    }


@router.post("/{team_id}/agents/{agent_id}")
async def add_agent_to_team(
    team_id: int,
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add an agent to a team"""
    result = await db.execute(
        select(Team).where(
            Team.id == team_id,
            Team.tenant_id == current_user.tenant_id
        )
    )
    team = result.scalar_one_or_none()

    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if team is None or agent is None:
        raise HTTPException(status_code=404, detail="Team or agent not found")

    if agent in team.agents:
        raise HTTPException(status_code=400, detail="Agent already in team")

    team.agents.append(agent)
    await db.commit()

    return {"message": "Agent added to team successfully"}


@router.delete("/{team_id}/agents/{agent_id}")
async def remove_agent_from_team(
    team_id: int,
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove an agent from a team"""
    result = await db.execute(
        select(Team).where(
            Team.id == team_id,
            Team.tenant_id == current_user.tenant_id
        )
    )
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None or agent not in team.agents:
        raise HTTPException(status_code=404, detail="Agent not in team")

    team.agents.remove(agent)
    await db.commit()

    return {"message": "Agent removed from team successfully"}