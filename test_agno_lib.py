from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools
import asyncio

async def test():
    agent = Agent(
        model=OpenRouter(id="stepfun/step-3.5-flash", api_key="sk-or-v1-dummy-key"),
        tools=[DuckDuckGoTools()]
    )
    result = agent.run("What is the weather in Rome today?")
    print(result.content)

asyncio.run(test())
