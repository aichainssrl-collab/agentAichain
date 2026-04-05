from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from agent_aichain.core.security import Security
from agent_aichain.core.tenant_context import set_current_tenant_id, reset_current_tenant_id
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.services.api_key_service import APIKeyService
from jose import JWTError
import structlog

logger = structlog.get_logger(__name__)

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = None
        
        # 1. Try to extract from Authorization header (JWT)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = Security.decode_token(token)
                tenant_id = payload.get("tenant_id")
            except JWTError:
                pass # Let the auth dependency handle the error and return 401
                
        # 2. Try to extract from X-API-Key header (API Key)
        elif "X-API-Key" in request.headers:
            api_key = request.headers.get("X-API-Key")
            try:
                async with AsyncSessionLocal() as session:
                    api_key_obj = await APIKeyService.verify_api_key(session, api_key)
                    if api_key_obj and api_key_obj.is_active:
                        # Find the user's tenant (since API keys are tied to a user who belongs to a tenant)
                        # We need to query the User model to get the tenant_id
                        from agent_aichain.models import User
                        from sqlalchemy import select
                        result = await session.execute(select(User).where(User.id == api_key_obj.owner_id))
                        user = result.scalar_one_or_none()
                        if user:
                            tenant_id = user.tenant_id
            except Exception as e:
                logger.error(f"Error extracting tenant from API Key: {e}")
        
        # Set context var if found
        token = None
        if tenant_id:
            token = set_current_tenant_id(tenant_id)
            
        try:
            response = await call_next(request)
            return response
        finally:
            # Always reset the context var after the request
            if token:
                reset_current_tenant_id(token)
