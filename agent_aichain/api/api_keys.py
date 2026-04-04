from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.models import User, APIKey
from agent_aichain.core.database import get_db
from agent_aichain.core.security import Security
from agent_aichain.api.auth import get_current_user
import secrets

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=dict)
async def create_api_key(
    name: str = Body(...),
    expires_in_days: Optional[int] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key for the current user"""
    # Generate a random API key
    api_key_raw = secrets.token_urlsafe(32)
    hashed_key = Security.get_password_hash(api_key_raw)

    # Calculate expiry date if specified
    expires_at = None
    if expires_in_days:
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    api_key = APIKey(
        name=name,
        key=api_key_raw,  # Store raw temporarily for response
        hashed_key=hashed_key,
        tenant_id=current_user.tenant_id,
        owner_id=current_user.id,
        expires_at=expires_at,
        is_active=True
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    # Return the raw key (only time it's visible)
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": api_key_raw,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "created_at": api_key.created_at.isoformat()
    }


@router.get("/", response_model=List[dict])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List API keys for the current user/tenant"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.tenant_id == current_user.tenant_id,
            APIKey.owner_id == current_user.id
        ).order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()

    return [
        {
            "id": ak.id,
            "name": ak.name,
            "is_active": ak.is_active,
            "expires_at": ak.expires_at.isoformat() if ak.expires_at else None,
            "last_used_at": ak.last_used_at.isoformat() if ak.last_used_at else None,
            "usage_count": ak.usage_count,
            "created_at": ak.created_at.isoformat()
        }
        for ak in api_keys
    ]


@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.tenant_id == current_user.tenant_id,
            APIKey.owner_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    await db.commit()

    return {"message": "API key revoked successfully"}