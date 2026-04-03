#!/usr/bin/env python3
"""
Seed the database with sample data for development/testing.
Usage: python scripts/seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.core.database import AsyncSessionLocal, init_db
from agent_aichain.models import Tenant, User, Agent, Team
from agent_aichain.core.security import Security


async def seed():
    """Create sample tenant and data"""
    print("Initializing database...")
    await init_db()
    print("Database initialized.\n")

    async with AsyncSessionLocal() as db:
        # Check if demo tenant already exists
        result = await db.execute(
            select(Tenant).where(Tenant.slug == "demo")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print("Demo tenant already exists. Skipping seed.")
            return

        print("Creating demo tenant...")
        tenant = Tenant(name="Demo Tenant", slug="demo", plan="free", max_agents=10, max_teams=5)
        db.add(tenant)
        await db.flush()

        # Create admin user
        admin = User(
            email="admin@demo.com",
            hashed_password=Security.get_password_hash("demo123"),
            tenant_id=tenant.id,
            is_superuser=True,
            is_active=True
        )
        db.add(admin)
        await db.flush()

        # Create sample agents
        agents = [
            Agent(
                name="Support Bot",
                role="assistant",
                model="gpt-4o",
                description="Customer support agent",
                instructions="Be helpful, polite, and concise.",
                tools=["search_kb", "create_ticket"],
                tenant_id=tenant.id
            ),
            Agent(
                name="Code Reviewer",
                role="reviewer",
                model="gpt-4o",
                description="Reviews code for bugs and security issues",
                instructions="Always explain why something is wrong. Suggest improvements.",
                tools=["linter", "security_scanner"],
                tenant_id=tenant.id
            ),
            Agent(
                name="Research Assistant",
                role="researcher",
                model="claude-3-opus",
                description="Performs web research and summarizes findings",
                instructions="Use web_search to find information. Provide sources.",
                tools=["web_search", "read_url"],
                tenant_id=tenant.id
            )
        ]
        db.add_all(agents)
        await db.flush()

        # Create sample team
        team = Team(
            name="Demo Team",
            mode="coordinate",
            description="A demo team for testing",
            config={"max_iterations": 5},
            tenant_id=tenant.id,
            agents=[agents[1], agents[2]]  # Code Reviewer + Research Assistant
        )
        db.add(team)
        await db.commit()

        print("✅ Demo tenant created!")
        print(f"   Tenant: {tenant.name} (slug: {tenant.slug})")
        print(f"   Admin email: {admin.email}")
        print(f"   Admin password: demo123")
        print(f"   Agents created: {len(agents)}")
        print(f"   Team created: {team.name}")
        print("\n⚠️  Change these credentials in production!")


if __name__ == "__main__":
    from sqlalchemy import select
    asyncio.run(seed())