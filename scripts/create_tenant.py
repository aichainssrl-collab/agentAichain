#!/usr/bin/env python3
"""
Script to create a new tenant with admin user.
Usage: python scripts/create_tenant.py --name "Tenant Name" --slug "tenant-slug" --email admin@example.com --password admin123
"""
import argparse
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.core.database import AsyncSessionLocal, init_db
from agent_aichain.services.tenant_service import TenantService
from agent_aichain.core.security import Security


async def create_tenant(
    name: str,
    slug: str,
    admin_email: str,
    admin_password: str
):
    """Create a new tenant with admin user"""
    print(f"Creating tenant '{name}' with slug '{slug}'...")

    async with AsyncSessionLocal() as db:
        try:
            tenant, admin = await TenantService.create_tenant(
                db=db,
                name=name,
                slug=slug,
                admin_email=admin_email,
                admin_password=admin_password
            )
            print("✅ Tenant created successfully!")
            print(f"   Tenant ID: {tenant.id}")
            print(f"   Tenant slug: {tenant.slug}")
            print(f"   Admin user ID: {admin.id}")
            print(f"   Admin email: {admin.email}")
            print("\n⚠️  Save these credentials!")

        except ValueError as e:
            print(f"❌ Error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1

    return 0


def main():
    parser = argparse.ArgumentParser(description="Create a new tenant")
    parser.add_argument("--name", required=True, help="Tenant name")
    parser.add_argument("--slug", required=True, help="Tenant slug (unique)")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")

    args = parser.parse_args()

    # Run init_db first
    asyncio.run(init_db())
    print("Database initialized.\n")

    return asyncio.run(create_tenant(
        name=args.name,
        slug=args.slug,
        admin_email=args.email,
        admin_password=args.password
    ))


if __name__ == "__main__":
    exit(main())