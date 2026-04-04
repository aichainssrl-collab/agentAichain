from datetime import timedelta
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from jose.exceptions import ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agent_aichain.models import User, Tenant
from agent_aichain.core.database import get_db
from agent_aichain.core.security import Security
from agent_aichain.core.config import settings
from agent_aichain.services.tenant_service import TenantService

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    try:
        payload = Security.decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if user is None or not Security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = Security.create_access_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register-tenant")
async def register_tenant(
    name: str = Body(...),
    slug: str = Body(...),
    admin_email: str = Body(...),
    admin_password: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Register a new tenant with admin user"""
    # Check if tenant slug already exists
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tenant slug already exists")

    # Check if admin email already exists
    result = await db.execute(select(User).where(User.email == admin_email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

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

    return {"message": "Tenant created successfully", "tenant_id": tenant.id, "admin_id": admin.id}