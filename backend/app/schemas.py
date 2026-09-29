from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import Category, ComplaintStatus, Priority


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
    reporter_contact: str | None = None
    category: Category
    priority: Priority
    status: ComplaintStatus
    ai_summary: str | None = None
    triaged_by: str | None = None
    triage_latency_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    model_config = ConfigDict(from_attributes=True)

class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class StatsResponse(BaseModel):
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total: int = 0
    cached: bool = False
    cache_ttl: int = 30

    def __getitem__(self, item: str) -> Any:
        if item == "total_complaints":
            return self.total
        return getattr(self, item)

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

class TriageOutcome(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    timestamp: datetime
    complaint_id: str | None = None

class MetaProvidersResponse(BaseModel):
    active_provider: str
    history: list[TriageOutcome] = []

