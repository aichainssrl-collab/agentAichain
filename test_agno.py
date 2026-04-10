import asyncio
from agno.agent import Agent as AgnoAgent
from agno.models.ollama import Ollama

async def main():
    agent = AgnoAgent(model=Ollama(id='qwen3.5:latest'))
    try:
        async for chunk in agent.arun('ciao', stream=True):
            print(chunk.content)
    except Exception as e:
        print('Error:', e)

asyncio.run(main())
