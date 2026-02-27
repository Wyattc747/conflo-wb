import json
import logging
from typing import Any, Optional
from functools import wraps

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-init Redis connection
_redis_client = None

async def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except ImportError:
            logger.warning("redis.asyncio not installed, caching disabled")
            return None
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache. Returns None on miss or error."""
    r = await _get_redis()
    if not r:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set a value in cache with TTL (seconds). Default 5 min."""
    r = await _get_redis()
    if not r:
        return False
    try:
        await r.set(key, json.dumps(value, default=str), ex=ttl)
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    r = await _get_redis()
    if not r:
        return False
    try:
        await r.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error: {e}")
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern. Returns count deleted."""
    r = await _get_redis()
    if not r:
        return 0
    try:
        keys = []
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await r.delete(*keys)
        return len(keys)
    except Exception as e:
        logger.warning(f"Cache delete pattern error: {e}")
        return 0


async def invalidate_project_cache(project_id: str):
    """Invalidate all cache entries for a project."""
    await cache_delete_pattern(f"project:{project_id}:*")


async def invalidate_org_cache(org_id: str):
    """Invalidate all cache entries for an org."""
    await cache_delete_pattern(f"org:{org_id}:*")


# Cache key builders
def project_key(project_id, tool: str, suffix: str = "") -> str:
    return f"project:{project_id}:{tool}" + (f":{suffix}" if suffix else "")

def org_key(org_id, resource: str) -> str:
    return f"org:{org_id}:{resource}"

def user_key(user_id, resource: str) -> str:
    return f"user:{user_id}:{resource}"
