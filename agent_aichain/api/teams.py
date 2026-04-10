from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from agent_aichain.models import Team, Agent, Tenant, team_agents
from agent_aichain.core.database import get_db
from agent_aichain.api.auth import get_current_user
from agent_aichain.models import User
from agent_aichain.services.graph_service import GraphService
from agent_aichain.core.rate_limit import TenantRateLimiter

router = APIRouter(prefix="/teams", tags=["teams"])

# 120 requests per minute per tenant for teams API
teams_rate_limiter = TenantRateLimiter(max_requests=120, window_seconds=60)


@router.post("/", response_model=dict)
async def create_team(
    background_tasks: BackgroundTasks,
    name: str = Body(...),
    mode: Optional[str] = Body("coordinate"),
    max_iterations: Optional[int] = Body(10),
    config: Optional[dict] = Body(None),
    agent_ids: Optional[List[int]] = Body(None),
    current_user: User = Depends(teams_rate_limiter),
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

    # Add agents to team if provided
    agent_count = 0
    if agent_ids:
        result = await db.execute(
            select(Agent).where(
                Agent.id.in_(agent_ids)
            )
        )
        agents = result.scalars().all()

        if len(agents) != len(agent_ids):
            raise HTTPException(status_code=400, detail="Some agents not found or not in tenant")

        team.agents = agents
        agent_count = len(agents)

    db.add(team)
    await db.commit()
    await db.refresh(team)
    # Refreshed team to get ID, agent_count is manually tracked to avoid lazy loading of agents

    # Sync Team to Graph DB
    background_tasks.add_task(
        GraphService.sync_team,
        team_id=team.id,
        name=team.name,
        tenant_id=team.tenant_id
    )
    
    # Sync agent links
    if agent_ids:
        for agent_id in agent_ids:
            background_tasks.add_task(
                GraphService.link_agent_to_team,
                agent_id=agent_id,
                team_id=team.id
            )

    return {
        "id": team.id,
        "name": team.name,
        "mode": team.mode,
        "tenant_id": team.tenant_id,
        "agent_count": agent_count
    }


@router.get("/", response_model=List[dict])
async def list_teams(
    current_user: User = Depends(teams_rate_limiter),
    db: AsyncSession = Depends(get_db)
):
    """List all teams for the current tenant"""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents))
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
    current_user: User = Depends(teams_rate_limiter),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific team with its agents"""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents))
        .where(
            Team.id == team_id
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


@router.delete("/{team_id}")
async def delete_team(
    team_id: int,
    current_user: User = Depends(teams_rate_limiter),
    db: AsyncSession = Depends(get_db)
):
    """Delete a team"""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents))
        .where(
            Team.id == team_id
        )
    )
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    await db.delete(team)
    await db.commit()

    return {"message": "Team deleted successfully"}


@router.post("/{team_id}/agents/{agent_id}")
async def add_agent_to_team(
    team_id: int,
    agent_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(teams_rate_limiter),
    db: AsyncSession = Depends(get_db)
):
    """Add an agent to a team"""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents))
        .where(
            Team.id == team_id
        )
    )
    team = result.scalar_one_or_none()

    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id
        )
    )
    agent = result.scalar_one_or_none()

    if team is None or agent is None:
        raise HTTPException(status_code=404, detail="Team or agent not found")

    if agent in team.agents:
        raise HTTPException(status_code=400, detail="Agent already in team")

    team.agents.append(agent)
    await db.commit()

    background_tasks.add_task(
        GraphService.link_agent_to_team,
        agent_id=agent.id,
        team_id=team.id
    )

    return {"message": "Agent added to team successfully"}


@router.delete("/{team_id}/agents/{agent_id}")
async def remove_agent_from_team(
    team_id: int,
    agent_id: int,
    current_user: User = Depends(teams_rate_limiter),
    db: AsyncSession = Depends(get_db)
):
    """Remove an agent from a team"""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents))
        .where(
            Team.id == team_id
        )
    )
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None or agent not in team.agents:
        raise HTTPException(status_code=404, detail="Agent not in team")

    team.agents.remove(agent)
    await db.commit()

    return {"message": "Agent removed from team successfully"}