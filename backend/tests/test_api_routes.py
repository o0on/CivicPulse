import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app
from fastapi import HTTPException

@pytest.fixture
def test_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")

@pytest.mark.asyncio
@patch("app.main.db_session", new_callable=lambda: None) # Mock DB session dependency
async def test_health_endpoint_200(mock_db, test_client):
    response = await test_client.get("/health")
    # Health endpoint shouldn't require DB but if it does, mock keeps it safe
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_health_returns_correct_schema(test_client):
    response = await test_client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ok", "healthy"]

@pytest.mark.asyncio
@patch("app.services.RateLimiter.is_allowed")
@patch("app.services.ComplaintService.create_complaint")
async def test_submit_complaint_success(mock_create, mock_rate_limit, test_client):
    mock_rate_limit.return_value = (True, 0)
    mock_create.return_value = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "text": "Water flooding from the street main pipe",
        "location": "Main St",
        "category": "water",
        "priority": "high",
        "status": "open",
        "ai_summary": "Flooding from pipe",
        "triaged_by": "simulated",
        "triage_latency_ms": 100
    }
    
    payload = {"text": "Water flooding from the street main pipe", "location": "Main St"}
    response = await test_client.post("/api/complaints", json=payload)
    
    assert response.status_code == 201
    assert response.json()["category"] == "water"

@pytest.mark.asyncio
@patch("app.services.RateLimiter.is_allowed")
async def test_submit_complaint_text_too_short(mock_rate_limit, test_client):
    mock_rate_limit.return_value = (True, 0)
    payload = {"text": "short", "location": "Main St"}
    response = await test_client.post("/api/complaints", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
@patch("app.services.RateLimiter.is_allowed")
async def test_submit_complaint_location_too_short(mock_rate_limit, test_client):
    mock_rate_limit.return_value = (True, 0)
    payload = {"text": "This is a valid long description of the issue", "location": "A"}
    response = await test_client.post("/api/complaints", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
@patch("app.services.ComplaintService.list_complaints")
async def test_list_complaints_pagination(mock_list, test_client):
    mock_list.return_value = ([], 0) # (items, total_count)
    response = await test_client.get("/api/complaints?page=2&page_size=10")
    assert response.status_code == 200

@pytest.mark.asyncio
@patch("app.services.StatsService.get_stats")
async def test_stats_returns_x_cache_header(mock_get_stats, test_client):
    mock_get_stats.return_value = ({"total": 5}, True) # returns (stats, is_cached)
    response = await test_client.get("/api/stats")
    assert response.status_code == 200
    assert response.headers.get("X-Cache") == "HIT"

@pytest.mark.asyncio
@patch("app.services.ComplaintService.update_status")
async def test_update_status_invalid_transition_409(mock_update, test_client):
    mock_update.side_effect = HTTPException(status_code=409, detail="Invalid transition from open to resolved")
    response = await test_client.patch("/api/complaints/123e4567-e89b-12d3-a456-426614174000/status", json={"status": "resolved"})
    assert response.status_code == 409
    assert "transition" in response.json()["detail"].lower()

@pytest.mark.asyncio
@patch("app.services.RateLimiter.is_allowed")
async def test_rate_limit_429(mock_is_allowed, test_client):
    mock_is_allowed.return_value = (False, 45) # (allowed, retry_after)
    response = await test_client.post("/api/complaints", json={"text": "Valid text description for rate limit test", "location": "Valid location"})
    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "45"

# Test: pagination boundary limits up to 100 items
