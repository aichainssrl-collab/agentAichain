import asyncio
from agent_aichain.workers.agno_wrapper import TenantAwareAgent

class MockAIModel:
    def __init__(self):
        self.provider = "openrouter"
        self.name = "pepos"
        self.api_key = "dummy_key"
        self.base_url = "https://openrouter.ai/stepfun/step-3.5-flash"
        self.max_tokens = 100
        self.config = "{}"

class MockAgent:
    def __init__(self):
        self.name = "pepos_agent"
        self.instructions = "say hello"
        self.tools = []

async def test():
    model = MockAIModel()
    agent = MockAgent()
    wrapper = TenantAwareAgent(tenant_id=1, agent_model=agent, ai_model=model, api_key="dummy_key", base_url="https://openrouter.ai/stepfun/step-3.5-flash")
    agno_model = wrapper._get_agno_model()
    print("Model ID:", agno_model.id)
    print("Base URL:", agno_model.base_url)

if __name__ == "__main__":
    asyncio.run(test())
