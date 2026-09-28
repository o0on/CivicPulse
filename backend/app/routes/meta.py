from datetime import datetime, timezone

from fastapi import APIRouter, Response

from app.core.config import settings
from app.core.database import check_db_health
from app.core.redis import check_redis_health
from app.schemas import HealthResponse, ReadyResponse

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


# Healthcheck pool telemetry
