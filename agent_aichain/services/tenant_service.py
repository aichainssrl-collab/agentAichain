from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from agent_aichain.models import Tenant, User
from agent_aichain.core.security import Security

class TenantService:
    """Service for tenant management"""

    @staticmethod
    async def create_tenant(
        db: AsyncSession,
        name: str,
        slug: str,
        admin_email: str,
        admin_password: str
    ) -> tuple[Tenant, User]:
        """Create a new tenant with admin user"""
        # Check if slug exists
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        if result.scalar_one_or_none():
            raise ValueError(f"Tenant slug '{slug}' already exists")

        # Check if email exists
        result = await db.execute(select(User).where(User.email == admin_email))
        if result.scalar_one_or_none():
            raise ValueError(f"Email '{admin_email}' already registered")

        # Create tenant
        tenant = Tenant(name=name, slug=slug)
        db.add(tenant)
        await db.flush()

        # Create admin user
        hashed_password = Security.get_password_hash(admin_password)
        admin = User(
            email=admin_email,
            hashed_password=hashed_password,
            tenant_id=tenant.id,
            is_superuser=True,
            is_active=True
        )
        db.add(admin)
        await db.commit()
        await db.refresh(tenant)
        await db.refresh(admin)

        return tenant, admin

    @staticmethod
    async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Tenant:
        """Get tenant by slug"""
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValueError(f"Tenant with slug '{slug}' not found")
        return tenant