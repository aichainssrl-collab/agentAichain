from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any

from agent_aichain.core.database import get_db
from agent_aichain.models.user import User
from agent_aichain.models.agent import Agent
from agent_aichain.models.team import Team
from agent_aichain.models.run import Run, RunStatus
from agent_aichain.api.auth import get_current_user

router = APIRouter(tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get statistics for the dashboard"""
    
    # Base conditions for tenant
    tenant_filter_agent = Agent.tenant_id == current_user.tenant_id
    tenant_filter_team = Team.tenant_id == current_user.tenant_id
    tenant_filter_run = Run.tenant_id == current_user.tenant_id

    # 1. Total Agents
    total_agents_result = await db.execute(select(func.count(Agent.id)).where(tenant_filter_agent))
    total_agents = total_agents_result.scalar_one_or_none() or 0

    # 2. Total Teams
    total_teams_result = await db.execute(select(func.count(Team.id)).where(tenant_filter_team))
    total_teams = total_teams_result.scalar_one_or_none() or 0

    # 3. Total Runs
    total_runs_result = await db.execute(select(func.count(Run.id)).where(tenant_filter_run))
    total_runs = total_runs_result.scalar_one_or_none() or 0

    # 4. Active Runs (pending or running)
    active_runs_result = await db.execute(
        select(func.count(Run.id)).where(
            tenant_filter_run,
            Run.status.in_([RunStatus.PENDING, RunStatus.RUNNING])
        )
    )
    active_runs = active_runs_result.scalar_one_or_none() or 0

    # 5. Recent Runs (limit 5) with Agent/Team names
    recent_runs_result = await db.execute(
        select(Run, Agent.name, Team.name)
        .outerjoin(Agent, Run.agent_id == Agent.id)
        .outerjoin(Team, Run.team_id == Team.id)
        .where(tenant_filter_run)
        .order_by(desc(Run.created_at))
        .limit(5)
    )
    
    recent_runs_data = []
    for run, agent_name, team_name in recent_runs_result.all():
        run_dict = {
            "id": run.id,
            "task": run.task,
            "status": run.status.value if hasattr(run.status, 'value') else run.status,
            "tokens_used": run.tokens_used,
            "cost": run.cost,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "agent_id": run.agent_id,
            "team_id": run.team_id,
            "agent_name": agent_name,
            "team_name": team_name
        }
        recent_runs_data.append(run_dict)

    return {
        "total_agents": total_agents,
        "total_teams": total_teams,
        "total_runs": total_runs,
        "active_runs": active_runs,
        "recent_runs": recent_runs_data
    }
