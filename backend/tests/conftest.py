import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.models import Category, Priority, ComplaintStatus
from app.providers.triage.base import TriageResult
from app.providers.triage.simulated import SimulatedTriage
from uuid import uuid4
from datetime import datetime, timezone

# Settings override for tests
TEST_SETTINGS = {
    'TRIAGE_PROVIDER': 'simulated',
    'SECRET_KEY': 'test-secret-key',
    'DATABASE_URL': 'postgresql+asyncpg://test:test@localhost:5432/test',
    'REDIS_URL': 'redis://localhost:6379/0',
}

@pytest.fixture
def mock_complaint():
    """Return a realistic mock Complaint ORM object."""
    complaint = MagicMock()
    complaint.id = uuid4()
    complaint.text = "Water main burst on main road, area flooded since morning"
    complaint.location = "Block 5 Gulshan"
    complaint.reporter_contact = None
    complaint.category = Category.water
    complaint.priority = Priority.high
    complaint.status = ComplaintStatus.open
    complaint.ai_summary = "Water main burst causing flooding"
    complaint.triaged_by = "simulated"
    complaint.triage_latency_ms = 45
    complaint.created_at = datetime.now(timezone.utc)
    complaint.updated_at = datetime.now(timezone.utc)
    return complaint

@pytest.fixture
def simulated_triage():
    return SimulatedTriage()

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.delete.return_value = 1
    redis.ping.return_value = True
    return redis

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo
