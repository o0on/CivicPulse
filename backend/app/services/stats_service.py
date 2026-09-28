import json
from redis.asyncio import Redis
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas import StatsResponse

class StatsService:
    def __init__(self, redis: Redis, repo: ComplaintRepository, ttl: int):
        self.redis = redis
        self.repo = repo
        self.ttl = ttl
    
    async def get_stats(self) -> tuple[StatsResponse, bool]:
        key = "stats:aggregate"
        cached = await self.redis.get(key)
        
        if cached:
            data = json.loads(cached)
            data["cached"] = True
            data["cache_ttl"] = self.ttl
            return StatsResponse(**data), True
            
        stats_data = await self.repo.get_stats()
        stats_dict = {
            "by_category": stats_data.get("by_category", {}),
            "by_priority": stats_data.get("by_priority", {}),
            "by_status": stats_data.get("by_status", {}),
            "total": stats_data.get("total", 0),
            "cached": False,
            "cache_ttl": self.ttl
        }
        
        await self.redis.set(key, json.dumps(stats_dict), ex=self.ttl)
        
        return StatsResponse(**stats_dict), False
    
    async def invalidate_stats(self) -> None:
        await self.redis.delete("stats:aggregate")
