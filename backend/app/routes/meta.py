import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import check_db_health
from app.core.redis import check_redis_health, get_redis
from app.schemas import HealthResponse, MetaProvidersResponse, ReadyResponse, TriageOutcome

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe — checks only process health. NEVER touches PostgreSQL or Redis."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version=settings.APP_VERSION,
    )


@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response) -> ReadyResponse:
    """Readiness probe — pings PostgreSQL (via engine pool) and Redis (via global pool)."""
    db_ok = await check_db_health()
    redis_ok = await check_redis_health()

    ready_status = "ready" if db_ok and redis_ok else "not_ready"
    if not (db_ok and redis_ok):
        response.status_code = 503

    return ReadyResponse(
        status=ready_status,
        postgres=db_ok,
        redis=redis_ok,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/meta/providers", response_model=MetaProvidersResponse)
async def get_meta_providers(redis: Redis = Depends(get_redis)) -> MetaProvidersResponse:
    """Surfaces active triage provider and last 20 triage outcomes (provider, latency ms, fallback)."""
    active_provider = settings.TRIAGE_PROVIDER
    raw_history = await redis.lrange("meta:triage_history", 0, 19)
    history: list[TriageOutcome] = []
    for item in raw_history:
        try:
            parsed = json.loads(item)
            history.append(TriageOutcome(**parsed))
        except Exception:
            continue

    return MetaProvidersResponse(
        active_provider=active_provider,
        history=history,
    )

