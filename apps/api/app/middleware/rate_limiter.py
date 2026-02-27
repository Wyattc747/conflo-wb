import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Rate limits per window (seconds)
RATE_LIMITS = {
    "default": (100, 60),        # 100 requests per 60 seconds
    "auth": (10, 60),            # 10 auth attempts per 60 seconds
    "upload": (20, 60),          # 20 uploads per 60 seconds
    "admin": (200, 60),          # 200 admin requests per 60 seconds
}


def _get_limit_key(path: str) -> str:
    if "/auth/" in path or "/login" in path:
        return "auth"
    if "/upload" in path or "/files" in path:
        return "upload"
    if "/admin/" in path:
        return "admin"
    return "default"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)

        try:
            from app.services.cache_service import _get_redis
            r = await _get_redis()
            if r:
                # Identify client by user_id if authenticated, else by IP
                user = getattr(request.state, "user", None)
                client_id = str(user["user_id"]) if user else (request.client.host if request.client else "unknown")

                limit_type = _get_limit_key(request.url.path)
                max_requests, window = RATE_LIMITS[limit_type]

                key = f"ratelimit:{limit_type}:{client_id}"

                current = await r.incr(key)
                if current == 1:
                    await r.expire(key, window)

                if current > max_requests:
                    ttl = await r.ttl(key)
                    return JSONResponse(
                        status_code=429,
                        content={"error": {"code": "RATE_LIMITED", "message": f"Too many requests. Try again in {ttl}s."}},
                        headers={"Retry-After": str(ttl)},
                    )
        except Exception as e:
            # Never block requests due to rate limiter errors
            logger.warning(f"Rate limiter error: {e}")

        return await call_next(request)
