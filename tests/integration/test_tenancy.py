import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from agent_aichain.models import Tenant, User, Agent, Base
from agent_aichain.core.config import Settings
from agent_aichain.core.security import Security

settings = Settings(_env_file=None)  # Use defaults for testing


@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a test database session"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_multi_tenancy_isolation(db_session):
    """Test that data is properly isolated between tenants"""

    # Create first tenant
    tenant1 = Tenant(name="Tenant 1", slug="tenant1")
    db_session.add(tenant1)
    await db_session.flush()

    # Create second tenant
    tenant2 = Tenant(name="Tenant 2", slug="tenant2")
    db_session.add(tenant2)
    await db_session.flush()

    # Create agents for tenant 1
    agent1_1 = Agent(name="Agent 1-1", role="assistant", model="gpt-4", tenant_id=tenant1.id)
    agent1_2 = Agent(name="Agent 1-2", role="coder", model="gpt-3.5-turbo", tenant_id=tenant1.id)
    db_session.add_all([agent1_1, agent1_2])

    # Create agents for tenant 2
    agent2_1 = Agent(name="Agent 2-1", role="researcher", model="claude-3-opus", tenant_id=tenant2.id)
    db_session.add(agent2_1)

    await db_session.commit()

    # Query agents for tenant 1 only
    from sqlalchemy import select
    result = await db_session.execute(select(Agent).where(Agent.tenant_id == tenant1.id))
    tenant1_agents = result.scalars().all()

    assert len(tenant1_agents) == 2
    assert all(a.tenant_id == tenant1.id for a in tenant1_agents)

    # Query agents for tenant 2 only
    result = await db_session.execute(select(Agent).where(Agent.tenant_id == tenant2.id))
    tenant2_agents = result.scalars().all()

    assert len(tenant2_agents) == 1
    assert tenant2_agents[0].tenant_id == tenant2.id

    # Ensure no cross-contamination
    assert agent1_1.id != agent2_1.id
    assert all(a.tenant_id != tenant2.id for a in tenant1_agents)
    assert all(a.tenant_id != tenant1.id for a in tenant2_agents)


from sqlalchemy import select

@pytest.mark.asyncio
async def test_user_belongs_to_tenant(db_session):
    """Test that users belong to correct tenant"""
    tenant = Tenant(name="Test Tenant", slug="test")
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        email="test@example.com",
        hashed_password=Security.get_password_hash("password123"),
        tenant_id=tenant.id,
        is_superuser=True
    )
    db_session.add(user)
    await db_session.commit()

    # Verify user belongs to tenant
    assert user.tenant_id == tenant.id
    assert user.tenant.slug == "test"

    # Query through relationship
    result = await db_session.execute(select(User).where(User.tenant.has(Tenant.slug == "test")))
    users = result.scalars().all()
    assert len(users) == 1
    assert users[0].email == "test@example.com"