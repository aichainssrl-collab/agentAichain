import asyncio
from sqlalchemy import select
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.models import AIModel

async def main():
    async with AsyncSessionLocal() as db:
        models = await db.execute(select(AIModel))
        for m in models.scalars():
            print(f"Model: {m.name}, Provider: {m.provider}, Base URL: {m.base_url}, API Key: {m.api_key}")

asyncio.run(main())
