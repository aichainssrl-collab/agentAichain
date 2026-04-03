import pytest
from agent_aichain.models import Tenant, User, Agent, Team, Run


def test_tenant_creation():
    """Test Tenant model creation"""
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        plan="free",
        max_agents=10,
        max_teams=5,
        is_active=True
    )
    assert tenant.name == "Test Tenant"
    assert tenant.slug == "test-tenant"
    assert tenant.is_active is True
    assert tenant.plan == "free"


def test_user_creation():
    """Test User model creation"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        tenant_id=1,
        is_active=True
    )
    assert user.email == "test@example.com"
    assert user.tenant_id == 1
    assert user.is_active is True


def test_agent_creation():
    """Test Agent model creation"""
    agent = Agent(
        name="Test Agent",
        role="assistant",
        model="gpt-4",
        tenant_id=1,
        config={"temperature": 0.7}
    )
    assert agent.name == "Test Agent"
    assert agent.role == "assistant"
    assert agent.model == "gpt-4"
    assert agent.tenant_id == 1


def test_team_creation():
    """Test Team model creation"""
    team = Team(
        name="Test Team",
        mode="coordinate",
        tenant_id=1,
        config={"max_iterations": 10}
    )
    assert team.name == "Test Team"
    assert team.mode == "coordinate"
    assert team.tenant_id == 1


def test_run_creation():
    """Test Run model creation"""
    run = Run(
        task="Test task",
        input={"query": "Hello"},
        status="pending",
        tenant_id=1
    )
    assert run.task == "Test task"
    assert run.input == {"query": "Hello"}
    assert run.status == "pending"
    assert run.tenant_id == 1