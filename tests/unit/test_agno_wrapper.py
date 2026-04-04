import pytest
from unittest.mock import patch, MagicMock
from agent_aichain.workers.agno_wrapper import TenantAwareAgent
from agent_aichain.models import Agent, AIModel
from dataclasses import dataclass

@pytest.mark.asyncio
async def test_run_with_agno_lib():
    agent = Agent(name="TestAgent", role="assistant", instructions="Test", model="pepos", tools=["web_search"])
    agent.id = 99
    
    ai_model = AIModel(
        name="pepos",
        provider="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key="test-key"
    )
    
    wrapper = TenantAwareAgent(
        agent_model=agent,
        tenant_id=1,
        api_key="mock",
        base_url="mock",
        ai_model=ai_model
    )
    
    @dataclass
    class MockRunResponse:
        content: str
        metrics: dict
        
    def mock_agent_run(self, task, *args, **kwargs):
        # We can assert that the task is passed properly
        assert "Hello" in task
        return MockRunResponse(content="Mocked Agno Response", metrics={"total_tokens": 42})

    with patch('agno.agent.Agent.run', new=mock_agent_run):
        result = await wrapper.run("Hello", {})
        
        assert result["output"]["response"] == "Mocked Agno Response"
        assert result["tokens_used"] == 42
