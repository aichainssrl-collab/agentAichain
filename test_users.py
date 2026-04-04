import asyncio
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.models import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(u.email)

asyncio.run(main())
