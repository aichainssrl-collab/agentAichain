import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agent_aichain.workers.agno_wrapper import TenantAwareAgent, TenantAwareTeam
from agent_aichain.models import Agent, AIModel, Team
from dataclasses import dataclass

@pytest.mark.asyncio
async def test_run_with_agno_lib():
    agent = Agent(name="TestAgent", role="assistant", instructions="Test", aimodel_id=1, tools=["web_search"])
    agent.id = 99
    
    # Create a mock AIModel instance to pass to TenantAwareAgent
    from agent_aichain.models.aimodel import AIModel
    mock_ai_model = AIModel(id=1, name="pepos", provider="openrouter", base_url="https://openrouter.ai/api/v1")
    
    wrapper = TenantAwareAgent(agent, 1, "test_key", "test_url", ai_model=mock_ai_model)
    
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


@pytest.mark.asyncio
async def test_arun_stream():
    agent = Agent(name="StreamAgent", role="assistant", instructions="Test Stream", aimodel_id=1, tools=[])
    agent.id = 100
    
    mock_ai_model = AIModel(id=1, name="pepos", provider="openrouter")
    wrapper = TenantAwareAgent(agent, 1, "test_key", "test_url", ai_model=mock_ai_model)
    
    @dataclass
    class MockChunk:
        content: str
        
    async def mock_arun(self, task, stream=False, *args, **kwargs):
        assert stream is True
        assert "Stream test" in task
        yield MockChunk(content="chunk1")
        yield MockChunk(content="chunk2")

    with patch('agno.agent.Agent.arun', new=mock_arun):
        chunks = []
        async for chunk in wrapper.arun_stream("Stream test", {}):
            chunks.append(chunk.content)
            
        assert chunks == ["chunk1", "chunk2"]


@pytest.mark.asyncio
async def test_team_run_with_agno_lib():
    # Setup team
    team_model = Team(name="TestTeam", mode="sequential", max_iterations=2, config={})
    team_model.id = 1
    
    # Setup members
    agent1 = Agent(name="Member1", role="assistant", instructions="Member 1", aimodel_id=1, tools=[])
    agent1.id = 1
    
    mock_ai_model = AIModel(id=1, name="pepos", provider="openrouter", base_url="https://openrouter.ai/api/v1")
    agent1.aimodel = mock_ai_model
    
    team_model.agents = [agent1]
    
    wrapper = TenantAwareTeam(team_model, 1, "test_key", "test_url")
    
    @dataclass
    class MockRunResponse:
        content: str
        metrics: dict
        
    def mock_team_run(self, task, *args, **kwargs):
        assert "Hello team" in task
        return MockRunResponse(content="Team Response", metrics={"total_tokens": 100})

    with patch('agno.team.team.Team.run', new=mock_team_run):
        result = await wrapper.run("Hello team", {})
        
        assert result["output"]["response"] == "Team Response"
        assert result["tokens_used"] == 100
