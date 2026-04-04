import asyncio
from agent_aichain.workers.agno_wrapper import TenantAwareAgent
from agent_aichain.models import Agent, AIModel

async def main():
    agent = Agent(name="CEO", role="boss", instructions="You are the CEO", model="pepos")
    agent.id = 1
    ai_model = AIModel(name="pepos", provider="openrouter", base_url="https://openrouter.ai/stepfun/step-3.5-flash", api_key="sk-or-v1-dummy-key")
    
    wrapper = TenantAwareAgent(agent_model=agent, tenant_id=1, api_key="", base_url="", ai_model=ai_model)
    result = await wrapper.run("Hello CEO", {})
    print(result)

asyncio.run(main())
