"""
main.py — FastAPI Application Entry Point.

The Election Journey Orchestrator API.
Serves both the REST API and the frontend SPA.

Run from project root: uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.logic.journey_manager import JourneyManager
from backend.logic.candidate_cards import parse_candidates, compare_candidates
from backend.logic.state_machine import JourneyState
from backend.services import civic_api, maps_api, calendar_api
from backend.utils.jargon_killer import translate, get_glossary
from backend.utils.sanitizer import sanitize
from backend.utils.date_helpers import (
    get_election_countdown,
    get_registration_deadlines,
    CURRENT_DATE,
)

# -----------------------------------------------------------------------
# App Initialisation
# -----------------------------------------------------------------------
app = FastAPI(
    title="Election Journey Orchestrator",
    description=(
        "A stateful election assistant API that manages a voter's "
        "progression from eligibility check to polling-day readiness."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------
# Serve Frontend
# -----------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# -----------------------------------------------------------------------
# Ephemeral Session Store (in-memory only — Zero-PII)
# -----------------------------------------------------------------------
_sessions: dict[str, JourneyManager] = {}


def _get_session(session_id: str) -> JourneyManager:
    """Retrieve a session or 404."""
    mgr = _sessions.get(session_id)
    if not mgr:
        raise HTTPException(404, "Session not found. Start a new journey.")
    return mgr


# -----------------------------------------------------------------------
# Request / Response Models
# -----------------------------------------------------------------------

class EligibilityRequest(BaseModel):
    session_id: str
    dob: str = Field(..., description="Date of birth ISO format YYYY-MM-DD")
    location: str = Field(..., description="Indian state or UT name")


class RegistrationRequest(BaseModel):
    session_id: str
    is_registered: bool


class CandidateRequest(BaseModel):
    session_id: str
    constituency: str


class SimulationRequest(BaseModel):
    session_id: str


class SimpleRequest(BaseModel):
    session_id: str


class DirectionsRequest(BaseModel):
    origin: str
    destination: str


class TranslateRequest(BaseModel):
    text: str


# -----------------------------------------------------------------------
# Health & Info
# -----------------------------------------------------------------------

@app.get("/api/health", tags=["Info"])
async def health():
    """Health check and election countdown."""
    return {
        "service": "Election Journey Orchestrator",
        "date": str(CURRENT_DATE),
        "countdown": get_election_countdown(),
        "status": "operational",
    }


@app.get("/api/deadlines", tags=["Info"])
async def deadlines():
    """Return key election deadlines."""
    return get_registration_deadlines()


# -----------------------------------------------------------------------
# Journey Endpoints
# -----------------------------------------------------------------------

@app.post("/api/journey/start", tags=["Journey"])
async def journey_start():
    """Create a new session and begin the journey."""
    mgr = JourneyManager()
    _sessions[mgr.session_id] = mgr
    return mgr.start_journey()


@app.post("/api/journey/eligibility", tags=["Journey"])
async def journey_eligibility(req: EligibilityRequest):
    """Stage 1 — Check eligibility (age + location)."""
    mgr = _get_session(req.session_id)
    try:
        return mgr.check_eligibility(req.dob, req.location)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/journey/registration", tags=["Journey"])
async def journey_registration(req: RegistrationRequest):
    """Stage 2 — Verify voter registration."""
    mgr = _get_session(req.session_id)
    try:
        return mgr.verify_registration(req.is_registered)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/journey/candidates", tags=["Journey"])
async def journey_candidates(req: CandidateRequest):
    """Stage 3 — Get candidate cards for a constituency."""
    mgr = _get_session(req.session_id)
    try:
        # Fetch from Civic API
        try:
            voter_info = await civic_api.get_voter_info(req.constituency)
        except civic_api.CivicAPIError:
            voter_info = civic_api.get_mock_voter_info(req.constituency)
            
        # Parse candidates from contests
        candidates_data = []
        for contest in voter_info.get("contests", []):
            for cand in contest.get("candidates", []):
                candidates_data.append({
                    "name": cand.get("name", "Unknown"),
                    "party": cand.get("party", "Unknown"),
                    "promises": ["Improve local infrastructure", "Better healthcare facilities", "Increase employment opportunities"], # Dummy promises since API doesn't provide them
                })
        
        return mgr.get_candidate_cards(req.constituency, candidates_data if candidates_data else None)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/journey/simulate", tags=["Journey"])
async def journey_simulate(req: SimulationRequest):
    """Stage 4 — Run polling simulation with VVPAT timer."""
    mgr = _get_session(req.session_id)
    try:
        return await mgr.run_polling_simulation()
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/journey/complete", tags=["Journey"])
async def journey_complete(req: SimulationRequest):
    """Finalise the journey → RESULTS_WAITING."""
    mgr = _get_session(req.session_id)
    try:
        return mgr.complete_journey()
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/journey/simple-mode", tags=["Journey"])
async def journey_simple_mode(req: SimpleRequest):
    """Toggle Emergency Simple Mode (≤ 15 word responses)."""
    mgr = _get_session(req.session_id)
    return mgr.toggle_simple_mode()


@app.get("/api/journey/status/{session_id}", tags=["Journey"])
async def journey_status(session_id: str):
    """Get current session state."""
    mgr = _get_session(session_id)
    return mgr.to_dict()


# -----------------------------------------------------------------------
# Google Services (Maps, Civic, Calendar)
# -----------------------------------------------------------------------

@app.post("/api/services/directions", tags=["Services"])
async def get_directions(req: DirectionsRequest):
    """Get time-to-booth and directions URL."""
    try:
        data = await maps_api.get_time_to_booth(req.origin, req.destination)
    except maps_api.MapsAPIError:
        data = maps_api.get_mock_time_to_booth(req.origin, req.destination)
    data["directions_url"] = maps_api.generate_directions_url(
        req.origin, req.destination
    )
    return data


@app.get("/api/services/polling-info/{state}", tags=["Services"])
async def get_polling_info(state: str):
    """Get polling station info (mock or live)."""
    try:
        return await civic_api.get_voter_info(state)
    except civic_api.CivicAPIError:
        return civic_api.get_mock_voter_info(state)


@app.get("/api/services/calendar-links", tags=["Services"])
async def get_calendar_links():
    """Get Google Calendar deep-links for all key dates."""
    return calendar_api.get_all_reminder_links()


# -----------------------------------------------------------------------
# Jargon Killer
# -----------------------------------------------------------------------

@app.post("/api/translate", tags=["Jargon"])
async def translate_text(req: TranslateRequest):
    """Translate government jargon to plain language."""
    return {"original": req.text, "translated": translate(req.text)}


@app.get("/api/glossary", tags=["Jargon"])
async def glossary():
    """Return the full jargon → plain language glossary."""
    return get_glossary()


# -----------------------------------------------------------------------
# Frontend SPA Serving
# -----------------------------------------------------------------------

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve the main SPA."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{path:path}", tags=["Frontend"])
async def serve_static(path: str):
    """Serve static frontend assets."""
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
