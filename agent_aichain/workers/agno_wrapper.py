from typing import Dict, Any, Optional
import httpx
from agent_aichain.models import Agent, Team
import structlog

logger = structlog.get_logger()


class TenantAwareAgent:
    """Wrapper around AGNO Agent that enforces tenant isolation"""

    def __init__(self, agent_model: Agent, tenant_id: int, api_key: str, base_url: str):
        self.agent_model = agent_model
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.base_url = base_url

    async def run(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent via AGNO API"""
        # Prepare payload with tenant isolation context
        payload = {
            "agent_id": f"tenant_{self.tenant_id}_agent_{self.agent_model.id}",
            "role": self.agent_model.role,
            "model": self.agent_model.model,
            "instructions": self.agent_model.instructions,
            "tools": self.agent_model.tools,
            "config": self.agent_model.config,
            "task": task,
            "input": input_data,
            "metadata": {
                "tenant_id": self.tenant_id,
                "agent_name": self.agent_model.name
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/agents/run",
                    json=payload,
                    headers=headers,
                    timeout=300.0
                )
                response.raise_for_status()
                result = response.json()

                logger.info(
                    "Agent run completed",
                    tenant_id=self.tenant_id,
                    agent_id=self.agent_model.id,
                    tokens=result.get("tokens_used", 0)
                )

                return {
                    "output": result.get("output", {}),
                    "tokens_used": result.get("tokens_used", 0),
                    "cost": result.get("cost", 0.0)
                }

            except httpx.HTTPError as e:
                logger.error(
                    "Agent run failed",
                    tenant_id=self.tenant_id,
                    agent_id=self.agent_model.id,
                    error=str(e)
                )
                raise


class TenantAwareTeam:
    """Wrapper around AGNO Team that enforces tenant isolation"""

    def __init__(self, team_model: Team, tenant_id: int, api_key: str, base_url: str):
        self.team_model = team_model
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.base_url = base_url

    async def run(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the team via AGNO API"""
        # Prepare payload with tenant isolation and team members
        payload = {
            "team_id": f"tenant_{self.tenant_id}_team_{self.team_model.id}",
            "mode": self.team_model.mode,
            "max_iterations": self.team_model.max_iterations,
            "config": self.team_model.config,
            "agents": [
                {
                    "id": f"tenant_{self.tenant_id}_agent_{a.id}",
                    "role": a.role,
                    "model": a.model,
                    "instructions": a.instructions,
                    "tools": a.tools,
                    "config": a.config
                }
                for a in self.team_model.agents
            ],
            "task": task,
            "input": input_data,
            "metadata": {
                "tenant_id": self.tenant_id,
                "team_name": self.team_model.name
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/teams/run",
                    json=payload,
                    headers=headers,
                    timeout=600.0
                )
                response.raise_for_status()
                result = response.json()

                logger.info(
                    "Team run completed",
                    tenant_id=self.tenant_id,
                    team_id=self.team_model.id,
                    tokens=result.get("tokens_used", 0)
                )

                return {
                    "output": result.get("output", {}),
                    "tokens_used": result.get("tokens_used", 0),
                    "cost": result.get("cost", 0.0)
                }

            except httpx.HTTPError as e:
                logger.error(
                    "Team run failed",
                    tenant_id=self.tenant_id,
                    team_id=self.team_model.id,
                    error=str(e)
                )
                raise