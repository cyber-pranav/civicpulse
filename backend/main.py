"""
@module Main
@description CivicPulse FastAPI application entry point.
             Registers all routers, middleware, and security headers.
"""
from __future__ import annotations

import os
import time
from datetime import date
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.routers import ai, nlp, translate, user, candidates
from backend.config import settings
from backend.utils.logger import Logger

from backend.logic.journey_manager import JourneyManager
from backend.logic.candidate_cards import parse_candidates, compare_candidates
from backend.logic.state_machine import JourneyState
from backend.services import civic_api, maps_api, calendar_api
from backend.utils.jargon_killer import translate as jargon_translate, get_glossary
from backend.utils.sanitizer import sanitize
from backend.utils.date_helpers import (
    get_election_countdown,
    get_registration_deadlines,
    CURRENT_DATE,
    COUNTING_DAY,
)

# ─── Rate Limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─── App Initialisation ───────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Indian election education assistant"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Security Headers Middleware ──────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    @description Adds security headers to every response.
    @param request: Request @param call_next: callable @returns Response
    """
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=(self)"
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response

# ─── Google Service Routers ───────────────────────────────────
app.include_router(ai.router)
app.include_router(nlp.router)
app.include_router(translate.router)
app.include_router(user.router)
app.include_router(candidates.router)

# ─── Frontend Dir ─────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# ─── Ephemeral Session Store (in-memory — Zero-PII) ──────────
_sessions: dict[str, JourneyManager] = {}


def _get_session(session_id: str) -> JourneyManager:
    """Retrieve a session or 404."""
    mgr = _sessions.get(session_id)
    if not mgr:
        raise HTTPException(404, "Session not found. Start a new journey.")
    return mgr


# ─── Request / Response Models ────────────────────────────────

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

class TranslateJargonRequest(BaseModel):
    text: str

# ─── Health & Info ────────────────────────────────────────────

@app.get("/api/health", tags=["Info"])
async def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "date": str(CURRENT_DATE),
        "countdown": get_election_countdown(),
        "counting_day": str(COUNTING_DAY),
    }

@app.get("/api/deadlines", tags=["Info"])
async def deadlines():
    return get_registration_deadlines()

# ─── Journey Endpoints ────────────────────────────────────────

@app.post("/api/journey/start", tags=["Journey"])
async def journey_start():
    mgr = JourneyManager()
    _sessions[mgr.session_id] = mgr
    return mgr.start_journey()

@app.post("/api/journey/eligibility", tags=["Journey"])
async def journey_eligibility(req: EligibilityRequest):
    mgr = _get_session(req.session_id)
    try:
        return mgr.check_eligibility(req.dob, req.location)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/journey/registration", tags=["Journey"])
async def journey_registration(req: RegistrationRequest):
    mgr = _get_session(req.session_id)
    try:
        return mgr.verify_registration(req.is_registered)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/journey/candidates", tags=["Journey"])
async def journey_candidates(req: CandidateRequest):
    mgr = _get_session(req.session_id)
    try:
        data_source = "civic_api"
        try:
            voter_info = await civic_api.get_voter_info(req.constituency)
        except (civic_api.CivicAPIError, Exception):
            voter_info = civic_api.get_mock_voter_info(req.constituency)
            data_source = "fallback_sample"

        candidates_data = []
        for contest in voter_info.get("contests", []):
            for cand in contest.get("candidates", []):
                candidates_data.append({
                    "name": cand.get("name", "Unknown"),
                    "party": cand.get("party", "Unknown"),
                    "promises": [
                        "Improve local infrastructure",
                        "Better healthcare facilities",
                        "Increase employment opportunities",
                    ],
                })

        result = mgr.get_candidate_cards(
            req.constituency,
            candidates_data if candidates_data else None,
        )
        result["_source"] = data_source
        return result
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/journey/simulate", tags=["Journey"])
async def journey_simulate(req: SimulationRequest):
    mgr = _get_session(req.session_id)
    try:
        return await mgr.run_polling_simulation()
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/journey/complete", tags=["Journey"])
async def journey_complete(req: SimulationRequest):
    mgr = _get_session(req.session_id)
    try:
        return mgr.complete_journey()
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/journey/simple-mode", tags=["Journey"])
async def journey_simple_mode(req: SimpleRequest):
    mgr = _get_session(req.session_id)
    return mgr.toggle_simple_mode()

@app.get("/api/journey/status/{session_id}", tags=["Journey"])
async def journey_status(session_id: str):
    mgr = _get_session(session_id)
    return mgr.to_dict()

# ─── Google Services (Maps, Civic, Calendar) ──────────────────

@app.post("/api/services/directions", tags=["Services"])
async def get_directions(req: DirectionsRequest):
    try:
        data = await maps_api.get_time_to_booth(req.origin, req.destination)
    except (maps_api.MapsAPIError, Exception):
        data = maps_api.get_mock_time_to_booth(req.origin, req.destination)
    data["directions_url"] = maps_api.generate_directions_url(
        req.origin, req.destination
    )
    return data

@app.get("/api/services/polling-info/{state}", tags=["Services"])
async def get_polling_info(state: str):
    try:
        result = await civic_api.get_voter_info(state)
        return result
    except (civic_api.CivicAPIError, Exception):
        mock_data = civic_api.get_mock_voter_info(state)
        mock_data["_fallback"] = True
        mock_data["_fallback_message"] = (
            "Live polling data is currently unavailable. "
            "Showing general guidelines for your area."
        )
        return mock_data

@app.get("/api/services/calendar-links", tags=["Services"])
async def get_calendar_links():
    return calendar_api.get_all_reminder_links()

@app.get("/api/services/calendar-ics", tags=["Services"])
async def get_calendar_ics():
    ics_content = calendar_api.generate_counting_day_ics()
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=counting_day_2026.ics",
        },
    )

# ─── Jargon Killer ────────────────────────────────────────────

@app.post("/api/jargon/translate", tags=["Jargon"])
async def translate_text(req: TranslateJargonRequest):
    return {"original": req.text, "translated": jargon_translate(req.text)}

@app.get("/api/jargon/glossary", tags=["Jargon"])
async def glossary():
    return get_glossary()

# ─── Frontend SPA Serving ─────────────────────────────────────

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{path:path}", tags=["Frontend"])
async def serve_static(path: str):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
