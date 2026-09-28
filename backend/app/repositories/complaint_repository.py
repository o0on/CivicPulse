from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Complaint, ComplaintStatus, Priority


class ComplaintCreate(BaseModel):
    text: str
    location: str
    reporter_contact: str | None = None
    category: Category
    priority: Priority
    ai_summary: str | None = None
    triaged_by: str | None = None
    triage_latency_ms: int

class ComplaintRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: ComplaintCreate) -> Complaint:
        complaint = Complaint(**data.model_dump())
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: UUID) -> Complaint | None:
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalars().first()

    async def list_complaints(
        self,
        status: ComplaintStatus | None,
        category: Category | None,
        priority: Priority | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Complaint], int]:
        query = select(Complaint)
        
        if status:
            query = query.where(Complaint.status == status)
        if category:
            query = query.where(Complaint.category == category)
        if priority:
            query = query.where(Complaint.priority == priority)
            
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.session.execute(count_query)).scalar() or 0
        
        query = query.order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        complaints = list(result.scalars().all())
        
        return complaints, total_count

    async def update_status(self, complaint_id: UUID, new_status: ComplaintStatus) -> Complaint | None:
        complaint = await self.get_by_id(complaint_id)
        if complaint:
            complaint.status = new_status
            await self.session.commit()
            await self.session.refresh(complaint)
        return complaint

    async def get_stats(self) -> dict:
        cat_result = await self.session.execute(
            select(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category)
        )
        by_category = {cat: count for cat, count in cat_result.all()}

        pri_result = await self.session.execute(
            select(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority)
        )
        by_priority = {pri: count for pri, count in pri_result.all()}

        stat_result = await self.session.execute(
            select(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
        )
        by_status = {status: count for status, count in stat_result.all()}

        total_result = await self.session.execute(select(func.count(Complaint.id)))
        total = total_result.scalar() or 0

        return {
            "by_category": by_category,
            "by_priority": by_priority,
            "by_status": by_status,
            "total": total
        }

# Index optimization: utilizes idx_complaints_status_priority
