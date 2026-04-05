from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, with_loader_criteria, Session
from sqlalchemy import event
from sqlalchemy.sql.expression import literal_column
from agent_aichain.core.config import settings
from agent_aichain.core.tenant_context import get_current_tenant_id

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

# Base for declarative models (imported from models.base)
from sqlalchemy import bindparam
from agent_aichain.models.base import Base

@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """Automatically add a filter for tenant_id to all queries."""
    import os
    if os.getenv("DISABLE_TENANT_FILTER") == "1":
        return

    tenant_id = get_current_tenant_id()
    if tenant_id is not None:
        # Create bindparam outside the lambda to ensure it's evaluated properly per-query without caching issues
        tenant_bind = bindparam("current_tenant_id", callable_=get_current_tenant_id)
        
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                Base,
                lambda cls: getattr(cls, "tenant_id") == tenant_bind if hasattr(cls, "tenant_id") else literal_column("1") == literal_column("1"),
                include_aliases=True,
                track_closure_variables=False
            )
        )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI - provides async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)