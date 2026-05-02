"""
conftest.py — Shared pytest fixtures for the CivicPulse test suite.

Provides:
  - FastAPI test client (async via httpx)
  - Pre-configured JourneyManager sessions
  - Common test constants
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app, _sessions
from backend.logic.journey_manager import JourneyManager
from backend.logic.state_machine import JourneyState


@pytest.fixture
def journey_manager() -> JourneyManager:
    """Create a fresh JourneyManager instance for unit testing."""
    return JourneyManager()


@pytest.fixture
def started_manager() -> JourneyManager:
    """Create a JourneyManager that has already started the journey."""
    mgr = JourneyManager()
    mgr.start_journey()
    return mgr


@pytest.fixture
def eligible_manager() -> JourneyManager:
    """Create a JourneyManager that has passed eligibility (age >= 18)."""
    mgr = JourneyManager()
    mgr.start_journey()
    mgr.check_eligibility("2000-06-15", "Maharashtra")
    return mgr


@pytest.fixture
def registered_manager() -> JourneyManager:
    """Create a JourneyManager that has verified registration."""
    mgr = JourneyManager()
    mgr.start_journey()
    mgr.check_eligibility("2000-06-15", "Maharashtra")
    mgr.verify_registration(True)
    return mgr


@pytest.fixture
def simulation_ready_manager() -> JourneyManager:
    """Create a JourneyManager ready for polling simulation."""
    mgr = JourneyManager()
    mgr.start_journey()
    mgr.check_eligibility("2000-06-15", "Maharashtra")
    mgr.verify_registration(True)
    mgr.get_candidate_cards("Mumbai North")
    return mgr


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear the session store before each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
async def async_client():
    """Provide an async HTTP client for integration testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
