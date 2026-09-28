import json

from redis.asyncio import Redis

from app.repositories.complaint_repository import ComplaintRepository
from app.schemas import StatsResponse


class StatsService:
    def __init__(self, redis: Redis, repo: ComplaintRepository, ttl: int = 30):
        self.redis = redis
        self.repo = repo
        self.ttl = ttl
    
    async def get_stats(self) -> tuple[StatsResponse, bool]:
        key = "stats:aggregate"
        cached = await self.redis.get(key)
        
        if cached:
            data = json.loads(cached) if isinstance(cached, str) else cached
            if isinstance(data, dict):
                data["cached"] = True
                data["cache_ttl"] = self.ttl
                total_val = data.get("total", data.get("total_complaints", 0))
                data["total"] = total_val
                return StatsResponse.model_validate(data), True
            return data, True
            
        stats_data = await self.repo.get_stats()
        total_val = stats_data.get("total", stats_data.get("total_complaints", 0))
        stats_dict = {
            "by_category": stats_data.get("by_category", {}),
            "by_priority": stats_data.get("by_priority", {}),
            "by_status": stats_data.get("by_status", {}),
            "total": total_val,
            "cached": False,
            "cache_ttl": self.ttl
        }
        
        await self.redis.set(key, json.dumps(stats_dict), ex=self.ttl)
        
        return StatsResponse(**stats_dict), False
    
    async def invalidate_stats(self) -> None:
        await self.redis.delete("stats:aggregate")
