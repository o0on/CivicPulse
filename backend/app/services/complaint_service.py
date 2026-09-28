from uuid import UUID

from fastapi import HTTPException

from app.models import Category, ComplaintStatus, Priority
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas import ComplaintCreate, ComplaintListResponse, ComplaintResponse
from app.services.rate_limiter import RateLimiter
from app.services.stats_service import StatsService
from app.services.triage_service import TriageService

ALLOWED_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.open: {ComplaintStatus.in_progress, ComplaintStatus.rejected},
    ComplaintStatus.in_progress: {ComplaintStatus.resolved, ComplaintStatus.rejected},
    ComplaintStatus.resolved: set(),
    ComplaintStatus.rejected: set(),
}

class ComplaintService:
    def __init__(
        self,
        repo: ComplaintRepository,
        triage_service: TriageService | None = None,
        rate_limiter: RateLimiter | None = None,
        stats_service: StatsService | None = None,
    ):
        self.repo = repo
        self.triage_service = triage_service
        self.rate_limiter = rate_limiter
        self.stats_service = stats_service
    
    def check_transition(self, current: ComplaintStatus, new_status: ComplaintStatus) -> None:
        if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
            current_val = current.value if hasattr(current, 'value') else str(current)
            new_val = new_status.value if hasattr(new_status, 'value') else str(new_status)
            raise HTTPException(
                status_code=409, 
                detail=f"Invalid transition from {current_val} to {new_val}"
            )

    async def submit_complaint(
        self,
        data: ComplaintCreate,
        client_ip: str,
    ) -> ComplaintResponse:
        return await self.create_complaint(data, client_ip)

    async def create_complaint(
        self,
        data: ComplaintCreate,
        client_ip: str,
    ) -> ComplaintResponse:
        if self.rate_limiter:
            allowed, retry_after = await self.rate_limiter.is_allowed(client_ip)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)}
                )
            
        if self.triage_service:
            result, triaged_by, latency = await self.triage_service.triage_complaint(data.text, data.location)
        else:
            from app.providers.triage.base import TriageResult
            result = TriageResult(category=Category.other, priority=Priority.normal, summary=data.text[:100], confidence=0.5)
            triaged_by, latency = "simulated", 10
        
        from app.repositories.complaint_repository import (
            ComplaintCreate as RepoComplaintCreate,
        )
        repo_data = RepoComplaintCreate(
            text=data.text,
            location=data.location,
            reporter_contact=data.reporter_contact,
            category=result.category,
            priority=result.priority,
            ai_summary=result.summary,
            triaged_by=triaged_by,
            triage_latency_ms=latency,
        )
        complaint = await self.repo.create(repo_data)
        
        if self.stats_service:
            await self.stats_service.invalidate_stats()
        return ComplaintResponse.model_validate(complaint)
    
    async def update_status(
        self,
        complaint_id: UUID,
        new_status: ComplaintStatus,
    ) -> ComplaintResponse:
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
            
        self.check_transition(complaint.status, new_status)
            
        updated = await self.repo.update_status(complaint_id, new_status)
        if self.stats_service:
            await self.stats_service.invalidate_stats()
        return ComplaintResponse.model_validate(updated)
    
    async def list_complaints(
        self,
        status: ComplaintStatus | None,
        category: Category | None,
        priority: Priority | None,
        page: int,
        page_size: int,
    ) -> ComplaintListResponse:
        items, total = await self.repo.list_complaints(status, category, priority, page, page_size)
        return ComplaintListResponse(
            items=[ComplaintResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    async def get_complaint(self, complaint_id: UUID) -> ComplaintResponse:
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return ComplaintResponse.model_validate(complaint)

# Audit logger entry point
