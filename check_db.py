import asyncio
from sqlalchemy import select
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.models import Agent, AIModel

async def main():
    async with AsyncSessionLocal() as db:
        agents = await db.execute(select(Agent))
        for a in agents.scalars():
            print(f"Agent: {a.name}, Model: {a.model}, Config: {a.config}")
        
        models = await db.execute(select(AIModel))
        for m in models.scalars():
            print(f"Model: {m.name}, Provider: {m.provider}, Base URL: {m.base_url}")

asyncio.run(main())
