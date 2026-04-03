from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from agent_aichain.models import APIKey, User
from agent_aichain.core.security import Security
from datetime import datetime, timedelta
import secrets

class APIKeyService:
    """Service for API key management"""

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        name: str,
        owner: User,
        expires_in_days: int = None
    ) -> tuple[APIKey, str]:
        """Create a new API key and return (api_key_object, raw_key)"""
        api_key_raw = secrets.token_urlsafe(32)
        hashed_key = Security.get_password_hash(api_key_raw)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key = APIKey(
            name=name,
            key=api_key_raw,
            hashed_key=hashed_key,
            tenant_id=owner.tenant_id,
            owner_id=owner.id,
            expires_at=expires_at,
            is_active=True
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return api_key, api_key_raw

    @staticmethod
    async def verify_api_key(db: AsyncSession, raw_key: str) -> Optional[APIKey]:
        """Verify an API key and return the associated record if valid"""
        result = await db.execute(select(APIKey))
        api_keys = result.scalars().all()

        for api_key in api_keys:
            if Security.verify_password(raw_key, api_key.hashed_key):
                # Check expiry
                if api_key.is_expired():
                    return None
                # Update last used
                api_key.last_used_at = datetime.utcnow()
                api_key.usage_count += 1
                await db.commit()
                return api_key
        return None