import time
from redis.asyncio import Redis

class RateLimiter:
    def __init__(self, redis: Redis, requests: int, window_seconds: int):
        self.redis = redis
        self.requests = requests
        self.window_seconds = window_seconds
        
    async def check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        key = f"rate:{client_ip}"
        now = time.time()
        window_start = now - self.window_seconds
        
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()
            
        current_requests = results[1]
        
        if current_requests >= self.requests:
            return False, int(self.window_seconds - (now - float(list(await self.redis.zrange(key, 0, 0, withscores=True))[0][1]))) if current_requests >= self.requests else self.window_seconds
        return True, 0
