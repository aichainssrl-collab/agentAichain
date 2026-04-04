import asyncio
from sqlalchemy import select, update
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.models import Agent

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Agent).where(Agent.name == "CEO"))
        agent = result.scalar_one_or_none()
        if agent:
            if "web_search" not in agent.tools:
                agent.tools = agent.tools + ["web_search"]
                await db.commit()
                print("Updated CEO agent tools to include web_search")
            else:
                print("CEO already has web_search")

asyncio.run(main())
