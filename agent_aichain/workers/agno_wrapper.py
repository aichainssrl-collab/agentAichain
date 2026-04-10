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
        # Initialize the TenantAwareAgent
        self.agent_model = agent_model
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.base_url = base_url
        self.ai_model = ai_model

    def _get_agno_model(self, ai_model):
        """Map database AIModel to Agno Model instance"""
        if not ai_model or not AGNO_AVAILABLE:
            return None
            
        provider = ai_model.provider.lower()
        if provider == "openrouter":
            base_url = ai_model.base_url
            model_id = ai_model.name
            
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
                api_key=ai_model.api_key,
                base_url=base_url
            )
        elif provider == "openai":
            return OpenAIChat(
                id=ai_model.name,
                api_key=ai_model.api_key,
                base_url=ai_model.base_url
            )
        elif provider == "anthropic":
            # Potrebbe servire il pacchetto anthropic per Agno
            try:
                from agno.models.anthropic import Anthropic
                return Anthropic(
                    id=ai_model.name,
                    api_key=ai_model.api_key,
                    base_url=ai_model.base_url
                )
            except ImportError:
                logger.warning("Agno non supporta Anthropic nativamente in questa versione o manca il pacchetto, fallback a OpenAIChat")
                return OpenAIChat(
                    id=ai_model.name,
                    api_key=ai_model.api_key,
                    base_url=ai_model.base_url
                )
        elif provider == "ollama":
            return Ollama(
                id=ai_model.name,
                host=ai_model.base_url or "http://localhost:11434"
            )
        else:
            # Requisito A3: Supporto universale modelli LLM
            # Se il provider è sconosciuto ma usa compatibilità OpenAI
            logger.info(f"Provider {provider} non riconosciuto nativamente, fallback a OpenAIChat per compatibilità")
            return OpenAIChat(
                id=ai_model.name,
                api_key=ai_model.api_key,
                base_url=ai_model.base_url
            )

    def _get_agno_tools(self, agent_model):
        """Map string tools from DB to Agno Tool instances"""
        if not AGNO_AVAILABLE:
            return []
            
        tools = []
        db_tools = agent_model.tools or []
        
        # Support default tools for CEO if empty
        if not db_tools and agent_model.name.lower() == "ceo":
            db_tools = ["web_search"]
            
        for tool_name in db_tools:
            tool_name = tool_name.lower().strip()
            if tool_name in ("web_search", "duckduckgo"):
                from agno.tools.duckduckgo import DuckDuckGoTools
                tools.append(DuckDuckGoTools())
            elif tool_name == "calculator":
                from agno.tools.calculator import CalculatorTools
                tools.append(CalculatorTools())
            elif tool_name == "python":
                from agno.tools.python import PythonTools
                tools.append(PythonTools())
            elif tool_name == "file":
                from agno.tools.file import FileTools
                tools.append(FileTools())
            elif tool_name == "wikipedia":
                try:
                    from agno.tools.wikipedia import WikipediaTools
                    tools.append(WikipediaTools())
                except ImportError:
                    logger.warning("WikipediaTools requested but 'wikipedia' package is missing. Run 'pip install wikipedia'")
            elif tool_name == "yfinance":
                try:
                    from agno.tools.yfinance import YFinanceTools
                    tools.append(YFinanceTools())
                except ImportError:
                    logger.warning("YFinanceTools requested but 'yfinance' package is missing. Run 'pip install yfinance'")
            else:
                logger.warning(f"Tool '{tool_name}' not supported or recognized.")

        return tools

    async def arun_stream(self, task: str, input_data: Dict[str, Any]):
        """Execute the agent and yield streaming responses"""
        if not self.ai_model or not AGNO_AVAILABLE:
            raise ValueError("Streaming is only available for native AGNO models")

        model = self._get_agno_model(self.ai_model)
        tools = self._get_agno_tools(self.agent_model)
        
        # Add current date to instructions to prevent date hallucinations
        d = datetime.now(zoneinfo.ZoneInfo("Europe/Rome"))
        giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        current_date_str = f"{giorni[d.weekday()]} {d.day} {mesi[d.month-1]} {d.year}"
        
        base_instructions = self.agent_model.instructions or f"You are a helpful assistant named {self.agent_model.name}."
        date_aware_instructions = f"INFO DI SISTEMA: Oggi è {current_date_str}.\n\n{base_instructions}"
        
        agent = AgnoAgent(
                name=self.agent_model.name,
                role=self.agent_model.role,
                instructions=date_aware_instructions,
                model=model,
                tools=tools,
                markdown=True,
                telemetry=False
            )

        # Build context from input_data if chat history is provided
        # Agno handles this differently natively, but we can prepend it to the task for stateless calls
        full_task = task
        if input_data and "chat_history" in input_data:
            history_str = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in input_data["chat_history"]])
            full_task = f"Previous conversation:\n{history_str}\n\nCurrent request:\n{task}"

        async for chunk in agent.arun(full_task, stream=True):
            yield chunk

    async def _run_with_agno_lib(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent using the official Agno Python library"""
        try:
            model = self._get_agno_model(self.ai_model)
            tools = self._get_agno_tools(self.agent_model)
            
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
                markdown=True,
                telemetry=False
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
            
            metrics = getattr(run_response, "metrics", None)
            tokens = 0
            if metrics:
                if hasattr(metrics, "total_tokens"):
                    tokens = metrics.total_tokens
                elif isinstance(metrics, dict):
                    tokens = metrics.get("total_tokens", 0)
            
            logger.info(
                "Agno library run completed",
                tenant_id=self.tenant_id,
                agent_id=self.agent_model.id,
                model=self.ai_model.name,
                tokens=tokens
            )
            
            # Extract response text
            response_content = run_response.content if hasattr(run_response, "content") else str(run_response)
            
            return {
                "output": {"response": response_content},
                "tokens_used": tokens,
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
        model_name = self.ai_model.name if self.ai_model else "unknown"
        payload = {
            "agent_id": f"tenant_{self.tenant_id}_agent_{self.agent_model.id}",
            "role": self.agent_model.role,
            "model": model_name,
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

    async def _run_with_agno_lib(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the team using the official Agno Python library"""
        try:
            from agno.team.team import Team as AgnoTeam
            
            # Create Agno agents for each team member
            members = []
            for agent_model in self.team_model.agents:
                ai_model = agent_model.aimodel
                
                # Setup instructions
                d = datetime.now(zoneinfo.ZoneInfo("Europe/Rome"))
                giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
                mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
                current_date_str = f"{giorni[d.weekday()]} {d.day} {mesi[d.month-1]} {d.year}"
                
                base_instructions = agent_model.instructions or f"You are a helpful assistant named {agent_model.name}."
                date_aware_instructions = f"INFO DI SISTEMA: Oggi è {current_date_str}.\n\n{base_instructions}"
                
                # To get tools and model, we use a dummy TenantAwareAgent
                dummy_agent = TenantAwareAgent(
                    agent_model=agent_model,
                    tenant_id=self.tenant_id,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    ai_model=ai_model
                )
                
                agno_model = dummy_agent._get_agno_model(ai_model)
                agno_tools = dummy_agent._get_agno_tools(agent_model)
                
                member = AgnoAgent(
                    name=agent_model.name,
                    role=agent_model.role,
                    instructions=date_aware_instructions,
                    model=agno_model,
                    tools=agno_tools,
                    markdown=True,
                    telemetry=False
                )
                members.append(member)
            
            # Create the team
            team_kwargs = {
                "name": self.team_model.name,
                "members": members,
                "markdown": True,
                "telemetry": False
            }
            
            # Use the first agent's model for the team orchestrator if available
            if members and members[0].model:
                team_kwargs["model"] = members[0].model
            
            team = AgnoTeam(**team_kwargs)
            
            # Run the team
            import asyncio
            loop = asyncio.get_event_loop()
            run_response = await loop.run_in_executor(None, team.run, task)
            
            metrics = getattr(run_response, "metrics", None)
            tokens = 0
            if metrics:
                if hasattr(metrics, "total_tokens"):
                    tokens = metrics.total_tokens
                elif isinstance(metrics, dict):
                    tokens = metrics.get("total_tokens", 0)
            
            logger.info(
                "Agno library team run completed",
                team_id=self.team_model.id,
                tenant_id=self.tenant_id,
                tokens=tokens
            )
            
            # Extract response
            response_content = run_response.content if hasattr(run_response, "content") else str(run_response)
            
            return {
                "output": {"response": response_content},
                "tokens_used": tokens,
                "cost": 0.0  # Optional cost calculation
            }
            
        except Exception as e:
            logger.error(
                "Agno library team run failed",
                tenant_id=self.tenant_id,
                team_id=self.team_model.id,
                error=str(e)
            )
            return {
                "output": {"response": f"Error running Agno Team: {str(e)}"},
                "tokens_used": 0,
                "cost": 0.0
            }

    async def run(self, task: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the team via API or Agno Library"""
        if AGNO_AVAILABLE:
            return await self._run_with_agno_lib(task, input_data)
        
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
                    "model": a.aimodel.name if a.aimodel else str(a.aimodel_id),
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