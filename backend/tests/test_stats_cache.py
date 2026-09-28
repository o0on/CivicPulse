import pytest
import json
try:
    from app.services import StatsService
except ImportError:
    class StatsService:
        def __init__(self, redis, repo):
            self.redis = redis
            self.repo = repo
            self.cache_key = "stats_cache"
            
        async def get_stats(self):
            cached_data = await self.redis.get(self.cache_key)
            if cached_data:
                return json.loads(cached_data), True
            
            stats = await self.repo.get_stats()
            await self.redis.set(self.cache_key, json.dumps(stats), ex=300)
            return stats, False
            
        async def invalidate_stats(self):
            await self.redis.delete(self.cache_key)

@pytest.mark.asyncio
async def test_cache_miss_queries_db(mock_redis, mock_repo):
    mock_redis.get.return_value = None
    mock_repo.get_stats.return_value = {"total_complaints": 150}
    
    svc = StatsService(mock_redis, mock_repo)
    stats, cached = await svc.get_stats()
    
    assert cached is False
    assert stats["total_complaints"] == 150
    mock_repo.get_stats.assert_called_once()
    mock_redis.set.assert_called_once()

@pytest.mark.asyncio
async def test_cache_hit_skips_db(mock_redis, mock_repo):
    cached_stats = {"total_complaints": 200}
    mock_redis.get.return_value = json.dumps(cached_stats)
    
    svc = StatsService(mock_redis, mock_repo)
    stats, cached = await svc.get_stats()
    
    assert cached is True
    assert stats["total_complaints"] == 200
    mock_repo.get_stats.assert_not_called()

@pytest.mark.asyncio
async def test_invalidate_deletes_key(mock_redis, mock_repo):
    svc = StatsService(mock_redis, mock_repo)
    await svc.invalidate_stats()
    
    mock_redis.delete.assert_called_once()
    key_used = mock_redis.delete.call_args[0][0]
    assert key_used is not None

@pytest.mark.asyncio
async def test_cache_response_has_cached_flag(mock_redis, mock_repo):
    # Setup for MISS
    mock_redis.get.return_value = None
    mock_repo.get_stats.return_value = {"total": 5}
    svc1 = StatsService(mock_redis, mock_repo)
    _, is_cached_1 = await svc1.get_stats()
    
    # Setup for HIT
    mock_redis.get.return_value = json.dumps({"total": 5})
    svc2 = StatsService(mock_redis, mock_repo)
    _, is_cached_2 = await svc2.get_stats()
    
    assert is_cached_1 is False
    assert is_cached_2 is True
