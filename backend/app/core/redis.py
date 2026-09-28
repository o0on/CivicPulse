import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_pool: redis.Redis | None = None

def create_redis_pool() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

async def init_redis():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = create_redis_pool()

async def close_redis():
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None

async def get_redis():
    if _redis_pool is None:
        await init_redis()
    yield _redis_pool

async def check_redis_health(client: redis.Redis | None = None) -> bool:
    try:
        r = client if client is not None else _redis_pool
        if r is None:
            await init_redis()
            r = _redis_pool
        await r.ping()  # type: ignore[union-attr]
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Resilience: pool reconnection handler
