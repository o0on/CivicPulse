from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models import Category, Priority, ComplaintStatus

class ComplaintCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000)
    location: str = Field(..., min_length=3, max_length=200)
    reporter_contact: str | None = Field(None, max_length=255)

class StatusUpdate(BaseModel):
    status: ComplaintStatus

class ComplaintResponse(BaseModel):
    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: ComplaintStatus
    ai_summary: str | None
    triaged_by: str | None
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class StatsResponse(BaseModel):
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]
    total: int
    cached: bool
    cache_ttl: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class ReadyResponse(BaseModel):
    status: str
    postgres: bool
    redis: bool
    timestamp: datetime

class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
