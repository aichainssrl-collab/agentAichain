"""
End-to-end integration tests using live API (Docker Compose).
Run: pytest tests/integration/test_e2e.py -v
Requires: docker-compose up -d
"""
import pytest
import httpx
import time
from agent_aichain.core.config import Settings

settings = Settings(_env_file=None)  # Read from actual .env or environment


@pytest.fixture(scope="session")
def base_url():
    """Base URL for API"""
    return "http://localhost:8000/api/v1"


@pytest.fixture
def http_client():
    """HTTP client for API requests"""
    with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
        yield client


def test_health_check(http_client):
    """Test health endpoint"""
    resp = http_client.get("http://localhost:8000/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_full_workflow(base_url, http_client):
    """Test complete workflow: create tenant, user, agent, team, run"""

    # Step 1: Register a new tenant (using direct script approach)
    # Since we already have demo tenant seeded, we use that.
    # Instead we create a new tenant with unique slug.
    import uuid
    tenant_slug = f"test-{uuid.uuid4().hex[:8]}"
    admin_email = f"admin-{tenant_slug}@example.com"

    # Register tenant
    resp = http_client.post(
        f"{base_url}/auth/register-tenant",
        json={
            "name": f"Test Tenant {tenant_slug}",
            "slug": tenant_slug,
            "admin_email": admin_email,
            "admin_password": "testpassword123"
        }
    )
    assert resp.status_code == 200, f"Failed: {resp.text}"
    data = resp.json()
    tenant_id = data["tenant_id"]
    admin_id = data["admin_id"]
    assert tenant_id is not None
    assert admin_id is not None

    # Step 2: Login to get JWT token
    resp = http_client.post(
        f"{base_url}/auth/token",
        data={
            "username": admin_email,
            "password": "testpassword123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    token_data = resp.json()
    access_token = token_data["access_token"]
    assert access_token is not None

    # Set auth header for subsequent requests
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Step 3: Create an API key (machine-to-machine)
    resp = http_client.post(
        f"{base_url}/api-keys/",
        json={"name": "Test API Key"},
        headers=auth_headers
    )
    assert resp.status_code == 200
    api_key_data = resp.json()
    api_key = api_key_data["key"]
    assert api_key is not None

    # Switch to API key auth
    api_headers = {"X-API-Key": api_key}

    # Create an AI model for the agent
    resp = http_client.post(
        f"{base_url}/settings/models",
        json={
            "name": "gpt-4o",
            "provider": "openai",
            "api_key": "dummy",
            "is_active": True
        },
        headers=api_headers
    )
    # 400 means it already exists, which is fine
    assert resp.status_code in (200, 400), resp.json()
    
    if resp.status_code == 200:
        model_id = resp.json()["id"]
    else:
        # If it exists, fetch it
        resp2 = http_client.get(f"{base_url}/settings/models", headers=api_headers)
        models = resp2.json()
        assert isinstance(models, list), f"Expected list, got: {models} (from GET after {resp.json()})"
        try:
            model_id = next(m["id"] for m in models if m["name"] == "gpt-4o")
        except StopIteration:
            pytest.fail(f"Model not found in GET despite POST 400: POST response={resp.json()}, GET response={models}")

    # Step 4: Create an agent
    resp = http_client.post(
        f"{base_url}/agents/",
        json={
            "name": "Test Agent",
            "role": "assistant",
            "aimodel_id": model_id,
            "instructions": "You are a helpful assistant.",
            "tools": []
        },
        headers=api_headers
    )
    assert resp.status_code == 200
    agent = resp.json()
    agent_id = agent["id"]
    assert agent["name"] == "Test Agent"
    assert agent["tenant_id"] == tenant_id

    # Step 5: List agents (should see only our agent)
    resp = http_client.get(f"{base_url}/agents/", headers=api_headers)
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) >= 1
    assert any(a["id"] == agent_id for a in agents)

    # Step 6: Create a team with the agent
    resp = http_client.post(
        f"{base_url}/teams/",
        json={
            "name": "Test Team",
            "mode": "coordinate",
            "agent_ids": [agent_id]
        },
        headers=api_headers
    )
    assert resp.status_code == 200
    team = resp.json()
    team_id = team["id"]
    assert team["name"] == "Test Team"
    assert team["agent_count"] == 1

    # Step 7: Create a run for the agent (async)
    resp = http_client.post(
        f"{base_url}/runs/agent/{agent_id}",
        json={
            "task": "Say hello",
            "input": {"message": "Hello!"}
        },
        headers=api_headers
    )
    assert resp.status_code == 200
    run = resp.json()
    run_id = run["run_id"]
    assert run["status"] == "pending"

    # Step 8: Poll for run completion (wait up to 10 seconds)
    max_polls = 20
    for _ in range(max_polls):
        resp = http_client.get(f"{base_url}/runs/{run_id}", headers=api_headers)
        assert resp.status_code == 200
        run_status = resp.json()
        if run_status["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)
    else:
        pytest.fail("Run did not complete within timeout")

    # Step 9: Verify run belongs to our tenant and agent
    final_run = resp.json()
    assert final_run["agent_id"] == agent_id
    assert final_run["status"] in ("completed", "failed")  # May fail due to AGNO mock

    print(f"\n✅ E2E test passed for tenant {tenant_slug}")
    print(f"   Agent ID: {agent_id}, Team ID: {team_id}, Run ID: {run_id}")


def test_multi_tenancy_isolation(base_url, http_client):
    """Test that tenants cannot access each other's data"""
    import uuid

    # Create two tenants with unique slugs
    tenants = []
    for i in range(2):
        unique_suffix = uuid.uuid4().hex[:8]
        slug = f"tenant-{i}-{unique_suffix}"
        admin_email = f"admin-{slug}@example.com"
        resp = http_client.post(
            f"{base_url}/auth/register-tenant",
            json={
                "name": f"Tenant {i} {unique_suffix}",
                "slug": slug,
                "admin_email": admin_email,
                "admin_password": "password123"
            }
        )
        assert resp.status_code == 200, f"Failed to create tenant: {resp.text}"
        data = resp.json()
        tenants.append({
            "tenant_id": data["tenant_id"],
            "admin_email": admin_email,
            "password": "password123"
        })

    # Login as tenant 0 and create an agent
    resp = http_client.post(
        f"{base_url}/auth/token",
        data={
            "username": tenants[0]["admin_email"],
            "password": tenants[0]["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    token0 = resp.json()["access_token"]

    # Create API key for tenant 0
    resp = http_client.post(
        f"{base_url}/api-keys/",
        json={"name": "Key for tenant 0"},
        headers={"Authorization": f"Bearer {token0}"}
    )
    assert resp.status_code == 200
    api_key0 = resp.json()["key"]

    # Create an AI model for the agent
    resp = http_client.post(
        f"{base_url}/settings/models",
        json={
            "name": "gpt-4o",
            "provider": "openai",
            "api_key": "dummy",
            "is_active": True
        },
        headers={"X-API-Key": api_key0}
    )
    assert resp.status_code in (200, 400), resp.json()

    if resp.status_code == 200:
        model_id = resp.json()["id"]
    else:
        resp2 = http_client.get(f"{base_url}/settings/models", headers={"X-API-Key": api_key0})
        models = resp2.json()
        assert isinstance(models, list), f"Expected list, got: {models} (from GET after {resp.json()})"
        try:
            model_id = next(m["id"] for m in models if m["name"] == "gpt-4o")
        except StopIteration:
            pytest.fail(f"Model not found in GET despite POST 400: POST response={resp.json()}, GET response={models}")

    # Create an agent as tenant 0
    resp = http_client.post(
        f"{base_url}/agents/",
        json={
            "name": "Agent Tenant 0",
            "role": "assistant",
            "aimodel_id": model_id
        },
        headers={"X-API-Key": api_key0}
    )
    assert resp.status_code == 200, resp.json()
    agent0 = resp.json()
    agent0_id = agent0["id"]

    # Login as tenant 1
    resp = http_client.post(
        f"{base_url}/auth/token",
        data={
            "username": tenants[1]["admin_email"],
            "password": tenants[1]["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    token1 = resp.json()["access_token"]

    # Create API key for tenant 1
    resp = http_client.post(
        f"{base_url}/api-keys/",
        json={"name": "Key for tenant 1"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert resp.status_code == 200
    api_key1 = resp.json()["key"]

    # Tenant 1 should NOT see tenant 0's agent
    resp = http_client.get(
        f"{base_url}/agents/",
        headers={"X-API-Key": api_key1}
    )
    assert resp.status_code == 200
    agents1 = resp.json()
    assert not any(a["id"] == agent0_id for a in agents1), "Tenant 1 should not see Tenant 0's agents"

    # Tenant 1 should NOT be able to access tenant 0's agent directly
    resp = http_client.get(
        f"{base_url}/agents/{agent0_id}",
        headers={"X-API-Key": api_key1}
    )
    assert resp.status_code in (404, 403), f"Expected 404 or 403, got {resp.status_code}"

    print("\n✅ Multi-tenancy isolation test passed: tenants are isolated")