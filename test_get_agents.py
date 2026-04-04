import httpx
import asyncio

async def main():
    base_url = "http://localhost:8000/api/v1"
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/auth/token", data={
            "username": "admin@demo.com",
            "password": "admin"
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            r = await client.get(f"{base_url}/agents/", headers=headers)
            print("Agents Status:", r.status_code)
            print("Agents Response:", r.text[:200])
            
            r2 = await client.get(f"{base_url}/teams/", headers=headers)
            print("Teams Status:", r2.status_code)
            print("Teams Response:", r2.text[:200])
        else:
            print("Login failed:", response.status_code, response.text)

asyncio.run(main())
