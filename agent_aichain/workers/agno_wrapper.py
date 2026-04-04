import json
import httpx
from datetime import datetime
import zoneinfo
from agent_aichain.models import Agent as DBAgent, Team
import structlog
from typing import Dict, Any, Optional

try:
    from agno.agent import Agent as AgnoAgent
    from agno.models.openai import OpenAIChat
    from agno.models.openrouter import OpenRouter
    from agno.models.ollama import Ollama
    from agno.tools.duckduckgo import DuckDuckGoTools
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

logger = structlog.get_logger()


class TenantAwareAgent:
    """Wrapper around AGNO Agent that enforces tenant isolation"""

    def __init__(self, agent_model: DBAgent, tenant_id: int, api_key: str, base_url: str, ai_model=None):
        self.agent_model = agent_model
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.base_url = base_url
        self.ai_model = ai_model

    def _get_agno_model(self):
        """Map database AIModel to Agno Model instance"""
        if not self.ai_model or not AGNO_AVAILABLE:
            return None
            
        provider = self.ai_model.provider.lower()
        if provider == "openrouter":
            base_url = self.ai_model.base_url
            model_id = self.ai_model.name
            
            # Fix user-provided OpenRouter URLs that point to the model page
            if base_url and "openrouter.ai" in base_url and not base_url.endswith("/api/v1"):
                # Extract the model ID from the URL (e.g., https://openrouter.ai/stepfun/step-3.5-flash -> stepfun/step-3.5-flash)
                parts = base_url.split("openrouter.ai/")
                if len(parts) > 1 and parts[1]:
                    extracted_model = parts[1].strip("/")
                    if extracted_model and extracted_model != "api/v1":
                        model_id = extracted_model
                base_url = "https://openrouter.ai/api/v1"
            elif not base_url:
                base_url = "https://openrouter.ai/api/v1"

            return OpenRouter(
                id=model_id,
                api_key=self.ai_model.api_key,
                base_url=base_url
            )
        elif provider == "openai":
            return OpenAIChat(
                id=self.ai_model.name,
                api_key=self.ai_model.api_key,
                base_url=self.ai_model.base_url
            )
        elif provider == "ollama":
            return Ollama(
                id=self.ai_model.name,
                host=self.ai_model.base_url or "http://localhost:11434"
            )
        else:
            return OpenAIChat(
                id=self.ai_model.name,
                api_key=self.ai_model.api_key,
                base_url=self.ai_model.base_url
            )

    def _get_agno_tools(self):
        """Map string tools from DB to Agno Tool instances"""
        if not AGNO_AVAILABLE:
            return []
            
        tools = []
        # Support both 'web_search' and checking if it should be added automatically
        db_tools = self.agent_model.tools or []
        if "web_search" in db_tools or self.agent_model.name.lower() == "ceo":
            # the user wants CEO to use web_search, so let's make sure it has it
            tools.append(DuckDuckGoTools())
        return tools

    async def _run_with_agno_lib(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent using the official Agno Python library"""
        try:
            model = self._get_agno_model()
            tools = self._get_agno_tools()
            
            # Add current date to instructions to prevent date hallucinations
            d = datetime.now(zoneinfo.ZoneInfo("Europe/Rome"))
            giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
            mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
            current_date_str = f"{giorni[d.weekday()]} {d.day} {mesi[d.month-1]} {d.year}"
            
            base_instructions = self.agent_model.instructions or f"You are a helpful assistant named {self.agent_model.name}."
            date_aware_instructions = f"INFO DI SISTEMA: Oggi è {current_date_str}.\n\n{base_instructions}"
            
            # Setup agent
            # We can use memory if we want, but formatting the history into the prompt works well for stateless API calls
            agent = AgnoAgent(
                name=self.agent_model.name,
                role=self.agent_model.role,
                instructions=date_aware_instructions,
                model=model,
                tools=tools,
                markdown=True
            )
            
            # Build chat history if provided
            chat_history = input_data.get("chat_history", [])
            
            full_task = task
            if chat_history:
                # Filter out empty messages and ensure correct format
                formatted_history = []
                for msg in chat_history:
                    role = msg.get('role', 'user')
                    # Map standard roles to what makes sense in a prompt
                    role_name = "User" if role == "user" else "Assistant (You)"
                    content = msg.get('content', '').strip()
                    if content:
                        formatted_history.append(f"{role_name}: {content}")
                
                if formatted_history:
                    history_text = "\n\n".join(formatted_history)
                    full_task = f"CONTESTO DELLA CONVERSAZIONE PRECEDENTE:\n{history_text}\n\n---\n\nNUOVA RICHIESTA DELL'UTENTE:\n{task}"
            
            # Run the agent (we use async run if available, or wrap synchronous run)
            import asyncio
            # Agno agent.run is synchronous, so we run it in a thread pool to avoid blocking the async loop
            loop = asyncio.get_event_loop()
            run_response = await loop.run_in_executor(None, agent.run, full_task)
            
            content = run_response.content if hasattr(run_response, 'content') else str(run_response)
            
            # Usage metrics might be available on the model or run_response
            tokens_used = 0
            if hasattr(run_response, 'metrics') and run_response.metrics:
                tokens_used = getattr(run_response.metrics, 'total_tokens', 0)
                
            logger.info(
                "Agno library run completed",
                tenant_id=self.tenant_id,
                agent_id=self.agent_model.id,
                model=self.ai_model.name,
                tokens=tokens_used
            )
            
            return {
                "output": {"response": content},
                "tokens_used": tokens_used,
                "cost": 0.0
            }
        except Exception as e:
            logger.error(
                "Agno library run failed",
                tenant_id=self.tenant_id,
                agent_id=self.agent_model.id,
                error=str(e)
            )
            return {
                "output": {"response": f"Error running Agno Agent: {str(e)}"},
                "tokens_used": 0,
                "cost": 0.0
            }

    async def run(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent via API or Agno Library"""
        if self.ai_model and AGNO_AVAILABLE:
            return await self._run_with_agno_lib(task, input_data)
            
        # Original Agno API payload...
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

        async with httpx.AsyncClient(verify=False) as client:
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

            except Exception as e:
                logger.error(
                    "Agent run failed (falling back to mock response)",
                    tenant_id=self.tenant_id,
                    agent_id=self.agent_model.id,
                    error=str(e)
                )
                # Fallback mock response for development since api.agno.io is a placeholder
                return {
                    "output": {"response": f"Hello from {self.agent_model.name}! (Mock response due to API connection error: {str(e)})"},
                    "tokens_used": 42,
                    "cost": 0.001
                }


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

        async with httpx.AsyncClient(verify=False) as client:
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

            except Exception as e:
                logger.error(
                    "Team run failed (falling back to mock response)",
                    tenant_id=self.tenant_id,
                    team_id=self.team_model.id,
                    error=str(e)
                )
                # Fallback mock response for development
                return {
                    "output": {"response": f"Hello from team {self.team_model.name}! (Mock response due to API connection error: {str(e)})"},
                    "tokens_used": 142,
                    "cost": 0.005
                }