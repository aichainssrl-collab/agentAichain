import pytest
import httpx
import uuid

@pytest.fixture(scope="session")
def base_url():
    """Base URL for API"""
    return "http://localhost:8000/api/v1"

@pytest.fixture
def http_client():
    """HTTP client for API requests"""
    with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
        yield client

def test_delete_team(base_url, http_client):
    """Test creating and deleting a team"""
    
    tenant_slug = f"test-teams-{uuid.uuid4().hex[:8]}"
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
    
    # Login to get JWT token
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
    
    # Set auth header
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create a team
    resp = http_client.post(
        f"{base_url}/teams/",
        json={
            "name": "Team to Delete",
            "mode": "coordinate",
            "agent_ids": []
        },
        headers=auth_headers
    )
    assert resp.status_code == 200
    team = resp.json()
    team_id = team["id"]
    
    # Verify team exists
    resp = http_client.get(f"{base_url}/teams/{team_id}", headers=auth_headers)
    assert resp.status_code == 200
    
    # Delete team
    resp = http_client.delete(f"{base_url}/teams/{team_id}", headers=auth_headers)
    assert resp.status_code == 200
    
    # Verify team is deleted
    resp = http_client.get(f"{base_url}/teams/{team_id}", headers=auth_headers)
    assert resp.status_code == 404
