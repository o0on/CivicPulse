from fastapi import APIRouter, Depends, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import StatsResponse
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.repositories.complaint_repository import ComplaintRepository
from app.services.stats_service import StatsService

router = APIRouter(tags=["stats"])

def get_stats_service(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    repo = ComplaintRepository(db)
    return StatsService(redis, repo, settings.STATS_CACHE_TTL)

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    response: Response,
    service: StatsService = Depends(get_stats_service)
):
    stats, cached = await service.get_stats()
    response.headers["X-Cache"] = "HIT" if cached else "MISS"
    return stats
