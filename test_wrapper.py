import asyncio
from agent_aichain.models.agent import Agent as AgentModel
from agent_aichain.models.aimodel import AIModel
from agent_aichain.workers.agno_wrapper import TenantAwareAgent

async def test():
    agent_model = AgentModel(id=4, name='CEO', role='assistant', instructions='')
    ai_model = AIModel(id=2, provider='ollama', name='qwen3.5:latest', base_url='http://host.docker.internal:11434')
    wrapper = TenantAwareAgent(agent_model=agent_model, tenant_id=1, ai_model=ai_model, api_key='mock', base_url='mock')
    try:
        async for chunk in wrapper.arun_stream('ciao', {}):
            if chunk.content:
                print(chunk.content, end='', flush=True)
        print()
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
