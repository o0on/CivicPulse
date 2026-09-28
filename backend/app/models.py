import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, MetaData, String, func
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Category(str, Enum):
    water = "water"
    electricity = "electricity"
    sanitation = "sanitation"
    roads = "roads"
    streetlights = "streetlights"
    other = "other"

class Priority(str, Enum):
    high = "high"
    normal = "normal"
    low = "low"

class ComplaintStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"

class TriagedBy(str, Enum):
    llm_groq = "llm:groq"
    llm_gemini = "llm:gemini"
    llm_ollama = "llm:ollama"
    rules = "rules"
    rules_fallback = "rules:fallback"
    simulated = "simulated"

class Base(DeclarativeBase):
    metadata = MetaData()

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[Category] = mapped_column(PG_ENUM(Category, name="category_enum", create_type=False), nullable=False)
    priority: Mapped[Priority] = mapped_column(PG_ENUM(Priority, name="priority_enum", create_type=False), nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(PG_ENUM(ComplaintStatus, name="status_enum", create_type=False), nullable=False, server_default='open')
    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    triage_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
