from fastapi import APIRouter, Depends, Request, Query
from uuid import UUID
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ComplaintCreate, ComplaintResponse, ComplaintListResponse, StatusUpdate
from app.models import ComplaintStatus, Category, Priority
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.repositories.complaint_repository import ComplaintRepository
from app.services.triage_service import TriageService
from app.services.rate_limiter import RateLimiter
from app.services.stats_service import StatsService
from app.services.complaint_service import ComplaintService
from app.providers.triage.factory import create_triage_provider
from app.providers.triage.rules import RuleBasedTriage

router = APIRouter(tags=["complaints"])

def get_complaint_service(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    repo = ComplaintRepository(db)
    provider = create_triage_provider()
    rules = RuleBasedTriage()
    triage = TriageService(provider, redis, rules)
    limiter = RateLimiter(redis, settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW_SECONDS)
    stats = StatsService(redis, repo, settings.STATS_CACHE_TTL)
    return ComplaintService(repo, triage, limiter, stats)

@router.post("/complaints", response_model=ComplaintResponse, status_code=201)
async def create_complaint(
    request: Request,
    data: ComplaintCreate,
    service: ComplaintService = Depends(get_complaint_service)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "127.0.0.1")
    ip = ip.split(",")[0].strip()
    return await service.submit_complaint(data, ip)

@router.get("/complaints", response_model=ComplaintListResponse)
async def list_complaints(
    status: ComplaintStatus | None = None,
    category: Category | None = None,
    priority: Priority | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ComplaintService = Depends(get_complaint_service)
):
    return await service.list_complaints(status, category, priority, page, page_size)

@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_complaint_service)
):
    return await service.get_complaint(complaint_id)

@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintResponse)
async def update_status(
    complaint_id: UUID,
    update: StatusUpdate,
    service: ComplaintService = Depends(get_complaint_service)
):
    return await service.update_status(complaint_id, update.status)
