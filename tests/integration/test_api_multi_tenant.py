import pytest
from fastapi.testclient import TestClient
from agent_aichain.main import app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from agent_aichain.models import Base, Tenant, User
from agent_aichain.core.security import Security

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def setup_tenants(db_session):
    """Setup test tenants and users"""
    # Create tenant 1
    tenant1 = Tenant(name="Tenant 1", slug="tenant1")
    db_session.add(tenant1)
    await db_session.flush()

    user1 = User(
        email="user1@tenant1.com",
        hashed_password=Security.get_password_hash("password1"),
        tenant_id=tenant1.id,
        is_active=True
    )
    db_session.add(user1)

    # Create tenant 2
    tenant2 = Tenant(name="Tenant 2", slug="tenant2")
    db_session.add(tenant2)
    await db_session.flush()

    user2 = User(
        email="user2@tenant2.com",
        hashed_password=Security.get_password_hash("password2"),
        tenant_id=tenant2.id,
        is_active=True
    )
    db_session.add(user2)

    await db_session.commit()

    return {
        "tenant1": tenant1,
        "user1": user1,
        "tenant2": tenant2,
        "user2": user2
    }


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "AgentAichain" in response.json()["message"]