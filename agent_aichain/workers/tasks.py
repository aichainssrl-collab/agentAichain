import asyncio
from typing import Dict, Any
from celery import current_task
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.models import Run, Agent, Team, Tenant
from agent_aichain.workers.agno_wrapper import TenantAwareAgent, TenantAwareTeam
from agent_aichain.core.config import settings
from agent_aichain.core.security import Security
import structlog

logger = structlog.get_logger()


async def execute_agent_run(run_id: int) -> Dict[str, Any]:
    """Execute an agent run and update the run record"""
    async with AsyncSessionLocal() as db:
        # Fetch run
        result = await db.execute(
            select(Run).where(Run.id == run_id)
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        # Fetch agent
        result = await db.execute(
            select(Agent).where(
                Agent.id == run.agent_id,
                Agent.tenant_id == run.tenant_id
            )
        )
        agent_model = result.scalar_one_or_none()
        if agent_model is None:
            raise ValueError(f"Agent {run.agent_id} not found")

        # Fetch tenant
        result = await db.execute(
            select(Tenant).where(Tenant.id == run.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValueError(f"Tenant {run.tenant_id} not found")

        # Update status to running
        run.status = "running"
        await db.commit()

        try:
            # Execute agent
            agent = TenantAwareAgent(
                agent_model=agent_model,
                tenant_id=tenant.id,
                api_key=settings.agno_api_key,
                base_url=settings.agno_base_url
            )

            result = await agent.run(
                task=run.task,
                input_data=run.input
            )

            # Update run with success
            run.output = result.get("output", {})
            run.status = "completed"
            run.tokens_used = result.get("tokens_used", 0)
            run.cost = result.get("cost", 0.0)

        except Exception as e:
            logger.error("Agent run failed", error=str(e), run_id=run_id)
            run.status = "failed"
            run.error = str(e)

        await db.commit()

        return {
            "run_id": run_id,
            "status": run.status,
            "output": run.output,
            "error": run.error
        }


async def execute_team_run(run_id: int) -> Dict[str, Any]:
    """Execute a team run and update the run record"""
    async with AsyncSessionLocal() as db:
        # Fetch run
        result = await db.execute(
            select(Run).where(Run.id == run_id)
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        # Fetch team with agents
        result = await db.execute(
            select(Team).where(
                Team.id == run.team_id,
                Team.tenant_id == run.tenant_id
            )
        )
        team_model = result.scalar_one_or_none()
        if team_model is None:
            raise ValueError(f"Team {run.team_id} not found")

        # Fetch tenant
        result = await db.execute(
            select(Tenant).where(Tenant.id == run.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValueError(f"Tenant {run.tenant_id} not found")

        # Update status to running
        run.status = "running"
        await db.commit()

        try:
            # Execute team
            team = TenantAwareTeam(
                team_model=team_model,
                tenant_id=tenant.id,
                api_key=settings.agno_api_key,
                base_url=settings.agno_base_url
            )

            result = await team.run(
                task=run.task,
                input_data=run.input
            )

            # Update run with success
            run.output = result.get("output", {})
            run.status = "completed"
            run.tokens_used = result.get("tokens_used", 0)
            run.cost = result.get("cost", 0.0)

        except Exception as e:
            logger.error("Team run failed", error=str(e), run_id=run_id)
            run.status = "failed"
            run.error = str(e)

        await db.commit()

        return {
            "run_id": run_id,
            "status": run.status,
            "output": run.output,
            "error": run.error
        }


@celery_app.task(bind=True, name="agent_run")
def run_agent_task(self, run_id: int):
    """Celery task to run an agent"""
    self.update_state(state="PROGRESS", meta={"run_id": run_id, "status": "starting"})

    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(execute_agent_run(run_id))
        loop.close()

        return result
    except Exception as e:
        logger.error("Celery agent task failed", error=str(e), run_id=run_id)
        raise


@celery_app.task(bind=True, name="team_run")
def run_team_task(self, run_id: int):
    """Celery task to run a team"""
    self.update_state(state="PROGRESS", meta={"run_id": run_id, "status": "starting"})

    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(execute_team_run(run_id))
        loop.close()

        return result
    except Exception as e:
        logger.error("Celery team task failed", error=str(e), run_id=run_id)
        raise