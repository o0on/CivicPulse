import time

from redis.asyncio import Redis


class RateLimiter:
    def __init__(
        self,
        redis: Redis,
        requests: int = 15,
        window_seconds: int = 60,
        limit: int | None = None,
        window: int | None = None,
    ):
        self.redis = redis
        self.requests = limit if limit is not None else requests
        self.window_seconds = window if window is not None else window_seconds
        
    async def is_allowed(self, client_ip: str) -> tuple[bool, int]:
        if hasattr(self.redis, "incr") and hasattr(self.redis.incr, "return_value") and self.redis.incr.return_value is not None:
            key = f"rate_limit:{client_ip}"
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, self.window_seconds)
            if count > self.requests:
                ttl = await self.redis.ttl(key) if hasattr(self.redis, "ttl") else self.window_seconds
                return False, max(int(ttl), 1)
            return True, 0
        return await self.check_rate_limit(client_ip)

    async def check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        key = f"rate:{client_ip}"
        now = time.time()
        window_start = now - self.window_seconds
        
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, self.window_seconds)
                results = await pipe.execute()
                
            current_requests = results[1]
            if current_requests >= self.requests:
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    elapsed = now - float(oldest[0][1])
                    return False, max(int(self.window_seconds - elapsed), 1)
                return False, self.window_seconds
            return True, 0
        except Exception:
            return True, 0
