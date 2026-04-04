import asyncio
from sqlalchemy import select
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.models import Agent

async def main():
    async with AsyncSessionLocal() as db:
        agents = await db.execute(select(Agent))
        for a in agents.scalars():
            print(f"Agent: {a.name}, Tools: {a.tools}")

asyncio.run(main())
