import time
from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis, ConnectionPool
from agent_aichain.core.config import settings
from agent_aichain.api.auth import get_current_user
from agent_aichain.models.user import User

# Global redis pool
redis_pool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)

class TenantRateLimiter:
    """
    Rate limiter dependency based on tenant_id using Redis fixed window.
    """
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, current_user: User = Depends(get_current_user)):
        redis = Redis(connection_pool=redis_pool)
        tenant_id = current_user.tenant_id
        
        # Simple fixed window
        current_window = int(time.time() / self.window_seconds)
        key = f"rate_limit:tenant:{tenant_id}:{current_window}"
        
        try:
            # We use a pipeline to ensure atomicity
            async with redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, self.window_seconds * 2) # Expire slightly after the window
                result = await pipe.execute()
                
            current_requests = result[0]
            
            if current_requests > self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds."
                )
        except HTTPException:
            raise
        except Exception as e:
            # Fallback if Redis is down, we might want to log and allow, or deny.
            # Allowing to prevent blocking all traffic if Redis fails
            import structlog
            logger = structlog.get_logger("rate_limit")
            logger.error("Redis rate limit error", error=str(e))
            
        return current_user
