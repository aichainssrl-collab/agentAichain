import asyncio
from agent_aichain.core.security import Security
from datetime import timedelta

async def test():
    token = Security.create_access_token(
        data={'sub': '1', 'tenant_id': 1},
        expires_delta=timedelta(minutes=30)
    )
    print(token)

asyncio.run(test())
