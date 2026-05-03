"""
test_integration.py — Integration Tests for the Journey Flow.

Validates end-to-end state transitions via the FastAPI HTTP API:
  - Eligibility → Registration upon valid form submission.
  - Full journey from start to completion.
  - API error handling and fallbacks.
"""
from __future__ import annotations
import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app, _sessions

@pytest.mark.asyncio
async def test_start_journey(async_client):
    """POST /api/journey/start creates a session."""
    r = await async_client.post("/api/journey/start")
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data["state"] == "ELIGIBILITY_CHECK"

@pytest.mark.asyncio
async def test_eligibility_to_registration(async_client):
    """Valid eligibility check transitions to REGISTRATION_VERIFIED."""
    r = await async_client.post("/api/journey/start")
    sid = r.json()["session_id"]
    r2 = await async_client.post("/api/journey/eligibility", json={
        "session_id": sid, "dob": "2000-06-15", "location": "Maharashtra"
    })
    assert r2.status_code == 200
    data = r2.json()
    assert data["state"] == "REGISTRATION_VERIFIED"
    assert data["age"] >= 18

@pytest.mark.asyncio
async def test_underage_to_civic_education(async_client):
    """Underage user transitions to CIVIC_EDUCATION."""
    r = await async_client.post("/api/journey/start")
    sid = r.json()["session_id"]
    r2 = await async_client.post("/api/journey/eligibility", json={
        "session_id": sid, "dob": "2010-06-15", "location": "Delhi"
    })
    data = r2.json()
    assert data["state"] == "CIVIC_EDUCATION"
    assert "civic_tips" in data

@pytest.mark.asyncio
async def test_full_journey_flow(async_client):
    """Complete journey: start → eligibility → register → candidates → simulate → complete."""
    r = await async_client.post("/api/journey/start")
    sid = r.json()["session_id"]
    await async_client.post("/api/journey/eligibility", json={
        "session_id": sid, "dob": "2000-01-15", "location": "Maharashtra"
    })
    await async_client.post("/api/journey/registration", json={
        "session_id": sid, "is_registered": True
    })
    await async_client.post("/api/journey/candidates", json={
        "session_id": sid, "constituency": "Mumbai North"
    })
    r5 = await async_client.post("/api/journey/simulate", json={"session_id": sid})
    assert r5.json()["state"] == "POLLING_READY"
    r6 = await async_client.post("/api/journey/complete", json={"session_id": sid})
    assert r6.json()["state"] == "RESULTS_WAITING"

@pytest.mark.asyncio
async def test_invalid_session_404(async_client):
    """Accessing a non-existent session returns 404."""
    r = await async_client.post("/api/journey/eligibility", json={
        "session_id": "nonexistent", "dob": "2000-01-01", "location": "Delhi"
    })
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """GET /api/health returns operational status."""
    r = await async_client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "operational"
    assert "counting_day" in data

@pytest.mark.asyncio
async def test_calendar_links(async_client):
    """GET /api/services/calendar-links returns entries including counting day."""
    r = await async_client.get("/api/services/calendar-links")
    assert r.status_code == 200
    links = r.json()
    assert len(links) >= 5
    titles = [l["title"] for l in links]
    assert any("Counting" in t for t in titles)

@pytest.mark.asyncio
async def test_calendar_ics_download(async_client):
    """GET /api/services/calendar-ics returns a valid .ics file."""
    r = await async_client.get("/api/services/calendar-ics")
    assert r.status_code == 200
    assert "text/calendar" in r.headers["content-type"]
    assert "BEGIN:VCALENDAR" in r.text
    assert "Counting Day" in r.text

@pytest.mark.asyncio
async def test_glossary_endpoint(async_client):
    """GET /api/jargon/glossary returns the jargon dictionary."""
    r = await async_client.get("/api/jargon/glossary")
    assert r.status_code == 200
    data = r.json()
    assert "constituency" in data

@pytest.mark.asyncio
async def test_translate_endpoint(async_client):
    """POST /api/jargon/translate replaces jargon."""
    r = await async_client.post("/api/jargon/translate", json={"text": "Check your Constituency"})
    assert r.status_code == 200
    data = r.json()
    assert "voting area" in data["translated"].lower()

@pytest.mark.asyncio
async def test_polling_info_fallback(async_client):
    """GET /api/services/polling-info gracefully falls back."""
    r = await async_client.get("/api/services/polling-info/Maharashtra")
    assert r.status_code == 200
    data = r.json()
    assert "contests" in data or "_fallback" in data
