# Examples

This document provides practical examples of using the AgentAichain API.

---

## Example 1: Create and Run a Support Agent

**Scenario:** You're building a customer support chatbot.

### Step 1: Get API Key

Login to your tenant dashboard and generate an API key, or use existing one.

```bash
API_KEY="your_api_key_here"
BASE_URL="https://your-api.example.com/api/v1"
```

### Step 2: Create an Agent

```bash
curl -X POST "${BASE_URL}/agents" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Bot v1",
    "role": "assistant",
    "model": "gpt-4o",
    "instructions": "You are a customer support agent for Acme Corp. Be polite, concise, and helpful. If you don''t know the answer, say so and offer to create a ticket.",
    "tools": ["search_knowledge_base", "create_ticket"],
    "config": {
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }'
```

Response:
```json
{
  "id": 42,
  "name": "Support Bot v1",
  "role": "assistant",
  "model": "gpt-4o"
}
```

Save the `id` (42) for next step.

### Step 3: Run the Agent

```bash
curl -X POST "${BASE_URL}/runs/agent/42" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Answer customer question",
    "input": {
      "customer_message": "I can''t log into my account. I keep getting 'Invalid password'.",
      "customer_id": "CUST-12345"
    }
  }'
```

Response (immediate):
```json
{
  "run_id": 150,
  "status": "pending",
  "celery_task_id": "a1b2c3d4-...",
  "agent_id": 42
}
```

### Step 4: Poll for Result

```bash
curl -X GET "${BASE_URL}/runs/150" \
  -H "X-API-Key: ${API_KEY}"
```

Response while running:
```json
{
  "id": 150,
  "status": "running",
  ...
}
```

Response when complete:
```json
{
  "id": 150,
  "task": "Answer customer question",
  "input": { "customer_message": "...", "customer_id": "CUST-12345" },
  "output": {
    "response": "I'm sorry to hear you're having trouble logging in. Here are some steps: 1) Ensure Caps Lock is off, 2) Use 'Forgot Password' to reset, 3) Clear your browser cache. Would you like me to create a support ticket?",
    "ticket_created": false
  },
  "status": "completed",
  "tokens_used": 187,
  "cost": 0.00187,
  "duration_ms": 3240
}
```

---

## Example 2: Research Team with Multiple Agents

**Scenario:** Deploy a team of specialized agents that collaborate on a research task.

### Step 1: Create Individual Agents

```bash
# Researcher agent
curl -X POST "${BASE_URL}/agents" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Researcher",
    "role": "researcher",
    "model": "claude-3-opus",
    "instructions": "Find information from trusted sources. Use web_search tool. Be thorough.",
    "tools": ["web_search", "read_url"],
    "config": { "top_k": 5 }
  }'

# Writer agent
curl -X POST "${BASE_URL}/agents" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Technical Writer",
    "role": "writer",
    "model": "gpt-4o",
    "instructions": "Synthesize research into clear, well-structured reports. Use markdown formatting.",
    "tools": [],
    "config": { "temperature": 0.5 }
  }'

# Reviewer agent
curl -X POST "${BASE_URL}/agents" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reviewer",
    "role": "reviewer",
    "model": "gpt-4o",
    "instructions": "Review drafts for accuracy, clarity, and completeness. Suggest improvements.",
    "tools": [],
    "config": {}
  }'
```

Save agent IDs: `1`, `2`, `3` (example).

### Step 2: Create a Team

```bash
curl -X POST "${BASE_URL}/teams" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Squad",
    "mode": "collaborate",
    "max_iterations": 5,
    "config": {
      "sharing_strategy": "broadcast",
      "max_rounds": 3
    },
    "agent_ids": [1, 2, 3]
  }'
```

Response:
```json
{
  "id": 5,
  "name": "Research Squad",
  "mode": "collaborate",
  "agent_count": 3
}
```

### Step 3: Run the Team

```bash
curl -X POST "${BASE_URL}/runs/team/5" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Research the impact of quantum computing on cryptography in 2025",
    "input": {
      "word_limit": 1000,
      "include_recent_developments": true
    }
  }'
```

Response:
```json
{
  "run_id": 151,
  "status": "pending",
  "celery_task_id": "f0e9...",
  "team_id": 5,
  "agent_count": 3
}
```

The team will collaborate:
1. Researcher searches web
2. Writer synthesizes findings into report
3. Reviewer checks for accuracy
4. (May iterate up to `max_iterations`)

---

## Example 3: Python SDK Wrapper

While we don't have an official SDK yet, here's a simple wrapper class:

```python
import httpx
import time
from typing import Optional, Dict, Any

class AgentAichainClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}
        self.client = httpx.Client(timeout=httpx.Timeout(30.0))

    def create_agent(self, name: str, model: str, role: str = "assistant",
                     instructions: str = "", tools: list = None, **kwargs) -> int:
        """Create agent and return ID"""
        resp = self.client.post(
            f"{self.base_url}/agents",
            headers=self.headers,
            json={
                "name": name,
                "role": role,
                "model": model,
                "instructions": instructions,
                "tools": tools or [],
                **kwargs
            }
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def run_agent(self, agent_id: int, task: str, input_data: Dict[str, Any] = None) -> Dict:
        """Run agent synchronously (polling)"""
        # Start run
        resp = self.client.post(
            f"{self.base_url}/runs/agent/{agent_id}",
            headers=self.headers,
            json={"task": task, "input": input_data or {}}
        )
        resp.raise_for_status()
        run_id = resp.json()["run_id"]

        # Poll until complete
        while True:
            resp = self.client.get(
                f"{self.base_url}/runs/{run_id}",
                headers=self.headers
            )
            resp.raise_for_status()
            run = resp.json()
            if run["status"] in ("completed", "failed", "cancelled"):
                return run
            time.sleep(1)

    def create_team(self, name: str, agent_ids: list, mode: str = "coordinate", **kwargs) -> int:
        """Create team and return ID"""
        resp = self.client.post(
            f"{self.base_url}/teams",
            headers=self.headers,
            json={
                "name": name,
                "mode": mode,
                "agent_ids": agent_ids,
                **kwargs
            }
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def run_team(self, team_id: int, task: str, input_data: Dict[str, Any] = None) -> Dict:
        """Run team synchronously (polling)"""
        resp = self.client.post(
            f"{self.base_url}/runs/team/{team_id}",
            headers=self.headers,
            json={"task": task, "input": input_data or {}}
        )
        resp.raise_for_status()
        run_id = resp.json()["run_id"]

        while True:
            resp = self.client.get(
                f"{self.base_url}/runs/{run_id}",
                headers=self.headers
            )
            resp.raise_for_status()
            run = resp.json()
            if run["status"] in ("completed", "failed", "cancelled"):
                return run
            time.sleep(2)

    def close(self):
        self.client.close()


# Usage
if __name__ == "__main__":
    client = AgentAichainClient(
        base_url="http://localhost:8000/api/v1",
        api_key="your_api_key"
    )

    # Create agent
    agent_id = client.create_agent(
        name="Code Reviewer",
        model="gpt-4o",
        role="code_reviewer",
        instructions="Review code for bugs, security issues, and best practices. Provide constructive feedback."
    )
    print(f"Created agent {agent_id}")

    # Run agent
    result = client.run_agent(
        agent_id=agent_id,
        task="Review this Python function",
        input_data={"code": "def add(a, b):\n    return a + b"}
    )
    print(f"Result: {result['output']}")
    client.close()
```

---

## Example 4: Bulk Create Tenants (Admin Script)

```python
# scripts/batch_create_tenants.py
import asyncio
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.services.tenant_service import TenantService

async def create_tenants_batch(tenants_data):
    """Create multiple tenants from CSV data"""
    async with AsyncSessionLocal() as db:
        for data in tenants_data:
            try:
                tenant, admin = await TenantService.create_tenant(
                    db=db,
                    name=data["name"],
                    slug=data["slug"],
                    admin_email=data["email"],
                    admin_password=data["password"]
                )
                print(f"✅ Created tenant {tenant.name} ({tenant.slug})")
            except ValueError as e:
                print(f"❌ Failed: {data['slug']} – {e}")

if __name__ == "__main__":
    tenants = [
        {
            "name": "Acme Corp",
            "slug": "acme",
            "email": "admin@acme.com",
            "password": "secure123"
        },
        {
            "name": "Beta Inc",
            "slug": "beta-inc",
            "email": "admin@beta.com",
            "password": "secure456"
        },
    ]
    asyncio.run(create_tenants_batch(tenants))
```

---

## Example 5: Streaming Response (Future Feature)

_Note: Streaming not yet implemented._

Planned WebSocket endpoint:

```javascript
const ws = new WebSocket('wss://api.example.com/ws/runs/150');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Token:', data.token);
  console.log('Delta:', data.delta);
};
```

---

## Example 6: Error Handling

```python
import httpx

client = httpx.Client(
    base_url="https://api.example.com/api/v1",
    headers={"X-API-Key": "your_key"}
)

try:
    response = client.post("/runs/agent/123", json={"task": "test"})
    response.raise_for_status()
    result = response.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Agent not found")
    elif e.response.status_code == 403:
        print("Access denied – check API key")
    elif e.response.status_code == 429:
        print("Rate limit exceeded")
    else:
        print(f"HTTP {e.response.status_code}: {e.response.text}")
except httpx.RequestError as e:
    print(f"Network error: {e}")
finally:
    client.close()
```

---

## Example 7: Pagination

```bash
# Get first page of runs (default limit 50)
curl -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/runs/?limit=20&offset=0"

# Get next page
curl -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/runs/?limit=20&offset=20"
```

---

## Example 8: Filtering Runs

```bash
# Get failed runs for a specific agent
curl -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/runs/?status=failed&agent_id=42"

# Get runs from last 24h (client-side filter)
curl -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/runs/?limit=100"
```

---

## Example 9: Authentication with JWT (User Flow)

```bash
# 1. Login to get JWT
curl -X POST "${BASE_URL}/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password"

# Response:
# { "access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer" }

# 2. Use JWT in subsequent requests
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  "${BASE_URL}/agents"
```

---

## Example 10: Docker Compose Local Development

```bash
# 1. Clone and setup
git clone https://github.com/aichainssrl-collab/agentAichain.git
cd agentAichain
cp .env.example .env
# Edit .env as needed

# 2. Start services
docker-compose up -d

# 3. Check logs
docker-compose logs -f api

# 4. Access API
curl http://localhost:8000/health

# 5. Create tenant
docker-compose exec api python scripts/create_tenant.py \
  --name "Demo" \
  --slug "demo" \
  --email "admin@demo.com" \
  --password "demo123"

# 6. Try API
API_KEY=$(docker-compose exec api python -c "from agent_aichain.services.api_key_service import APIKeyService; from agent_aichain.core.database import AsyncSessionLocal; import asyncio; async def get_key(): async with AsyncSessionLocal() as db: from agent_aichain.models import User; result = await db.execute(select(User).where(User.email=='admin@demo.com')); user=result.scalar_one(); key,_=await APIKeyService.create_api_key(db, 'test', user); print(key.key); asyncio.run(get_key())")

curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/agents

# 7. Stop
docker-compose down
```

---

*For more advanced scenarios, see [docs/OPERATIONS.md](OPERATIONS.md).*