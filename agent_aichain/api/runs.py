from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.models import Run, Agent, Team, Tenant
from agent_aichain.core.database import get_db
from agent_aichain.api.auth import get_current_user
from agent_aichain.models import User
from agent_aichain.workers.tasks import run_agent_task, run_team_task

router = APIRouter(prefix="/runs", tags=["runs"])


from fastapi.responses import StreamingResponse
import json
from agent_aichain.workers.agno_wrapper import TenantAwareAgent
from agent_aichain.models import AIModel
from agent_aichain.core.config import settings

@router.post("/agent/{agent_id}/stream")
async def stream_agent_run(
    agent_id: int,
    task: str = Body(...),
    input: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute an agent and stream the response back using SSE"""
    # Verify agent belongs to tenant and fetch model
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await db.execute(
        select(AIModel).where(AIModel.id == agent.aimodel_id)
    )
    ai_model = result.scalar_one_or_none()

    if not ai_model:
        raise HTTPException(status_code=400, detail="AI Model not configured for this agent")

    # Create run record
    run = Run(
        task=task,
        input=input or {},
        status="running",
        tenant_id=current_user.tenant_id,
        agent_id=agent.id
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    async def event_generator():
        wrapper = TenantAwareAgent(
            agent_model=agent,
            tenant_id=current_user.tenant_id,
            api_key=settings.agno_api_key,
            base_url=settings.agno_base_url,
            ai_model=ai_model
        )
        
        full_content = ""
        try:
            async for chunk in wrapper.arun_stream(task, input or {}):
                if chunk.content:
                    full_content += chunk.content
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
            
            # Save the run outcome
            run.status = "completed"
            run.output = {"response": full_content}
            # Note: For accurate metrics we'd need to compute them, ignoring for stream
            
            yield f"data: {json.dumps({'done': True, 'run_id': run.id})}\n\n"
        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # We need to use a new session to update the DB because the original session 
            # might be closed by the time streaming finishes, but for simplicity we rely on 
            # the current session. In a production app, we'd use a background task or context manager.
            # Here we just try to commit if session is still valid.
            try:
                db.add(run)
                await db.commit()
            except Exception:
                pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/agent/{agent_id}")
async def create_agent_run(
    agent_id: int,
    task: str = Body(...),
    input: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a run for a specific agent (async via Celery)"""
    # Verify agent belongs to tenant
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == current_user.tenant_id
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create run record
    run = Run(
        task=task,
        input=input or {},
        status="pending",
        tenant_id=current_user.tenant_id,
        agent_id=agent.id
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Trigger async task
    task_id = run_agent_task.delay(run.id)

    # Update run with celery task ID
    run.celery_task_id = task_id.id
    await db.commit()

    return {
        "run_id": run.id,
        "status": run.status,
        "celery_task_id": task_id.id,
        "agent_id": agent.id
    }


@router.post("/team/{team_id}")
async def create_team_run(
    team_id: int,
    task: str = Body(...),
    input: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a run for a team of agents (async via Celery)"""
    # Verify team belongs to tenant
    result = await db.execute(
        select(Team).where(
            Team.id == team_id,
            Team.tenant_id == current_user.tenant_id
        )
    )
    team = result.scalar_one_or_none()

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if not team.agents:
        raise HTTPException(status_code=400, detail="Team has no agents")

    # Create run record
    run = Run(
        task=task,
        input=input or {},
        status="pending",
        tenant_id=current_user.tenant_id,
        team_id=team.id
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Trigger async task
    task_id = run_team_task.delay(run.id)

    # Update run with celery task ID
    run.celery_task_id = task_id.id
    await db.commit()

    return {
        "run_id": run.id,
        "status": run.status,
        "celery_task_id": task_id.id,
        "team_id": team.id,
        "agent_count": len(team.agents)
    }


@router.get("/{run_id}")
async def get_run(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the status and result of a run"""
    result = await db.execute(
        select(Run).where(
            Run.id == run_id,
            Run.tenant_id == current_user.tenant_id
        )
    )
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "id": run.id,
        "task": run.task,
        "input": run.input,
        "output": run.output,
        "error": run.error,
        "status": run.status,
        "tokens_used": run.tokens_used,
        "cost": run.cost,
        "duration_ms": run.duration_ms,
        "metadata": run.run_metadata,
        "agent_id": run.agent_id,
        "team_id": run.team_id,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "celery_task_id": run.celery_task_id
    }


@router.get("/", response_model=list)
async def list_runs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    agent_id: Optional[int] = None,
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List runs for the current tenant with optional filters"""
    query = select(Run).where(Run.tenant_id == current_user.tenant_id)

    if status:
        query = query.where(Run.status == status)
    if agent_id:
        query = query.where(Run.agent_id == agent_id)
    if team_id:
        query = query.where(Run.team_id == team_id)

    query = query.order_by(Run.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    runs = result.scalars().all()

    return [
        {
            "id": r.id,
            "task": r.task,
            "status": r.status,
            "agent_id": r.agent_id,
            "team_id": r.team_id,
            "tokens_used": r.tokens_used,
            "cost": r.cost,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in runs
    ]