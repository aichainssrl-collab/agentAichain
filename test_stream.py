import asyncio
import os
import sys

# Setup django/fastapi env if needed, or just test httpx stream
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "admin@demo.com", "password": "password"} # I don't know the password...
        )
        print("login:", response.status_code, response.text)

asyncio.run(test())
