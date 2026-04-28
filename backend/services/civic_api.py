"""
civic_api.py — Google Civic Information API Wrapper.

Async client for polling stations, candidate lists, and election metadata.
Zero-PII: addresses used only in-flight, never persisted.
"""

from __future__ import annotations
import os
from typing import Any, Optional
import httpx

CIVIC_API_BASE = "https://www.googleapis.com/civicinfo/v2"
_API_KEY: Optional[str] = os.environ.get("GOOGLE_CIVIC_API_KEY")
REQUEST_TIMEOUT: float = 10.0


class CivicAPIError(Exception):
    """Raised on Google Civic API errors."""


async def get_voter_info(address: str, election_id: str = "2000") -> dict[str, Any]:
    """Look up voter info (polling locations, contests, candidates)."""
    _ensure_api_key()
    params = {"key": _API_KEY, "address": address, "electionId": election_id}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{CIVIC_API_BASE}/voterinfo", params=params)
        _handle_response(resp)
        return resp.json()


async def list_elections() -> list[dict[str, Any]]:
    """Fetch available elections."""
    _ensure_api_key()
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{CIVIC_API_BASE}/elections", params={"key": _API_KEY})
        _handle_response(resp)
        return resp.json().get("elections", [])


async def get_representatives(address: str) -> dict[str, Any]:
    """Fetch political representatives for an address."""
    _ensure_api_key()
    params = {"key": _API_KEY, "address": address}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{CIVIC_API_BASE}/representatives", params=params)
        _handle_response(resp)
        return resp.json()


def get_mock_voter_info(state: str) -> dict[str, Any]:
    """Mock voter info for demos without an API key."""
    # Generate dynamic-looking names based on the state/district name length and characters
    prefix = state.capitalize()[:4] if state else "Local"
    
    return {
        "election": {"id": "IN2026-PHASE2", "name": "Indian General Election 2026 — Phase II", "electionDay": "2026-04-29"},
        "pollingLocations": [{"address": {"locationName": f"Govt Primary School, Ward 12, {state}", "line1": "Main Road, Block B", "city": "Sample City", "state": state, "zip": "700001"}, "pollingHours": "7:00 AM – 6:00 PM", "notes": "Wheelchair accessible. Bring original Voter ID."}],
        "contests": [{"office": f"Member of Parliament — {state}", "candidates": [
            {"name": f"{prefix} Sharma", "party": "National Progress Party"}, 
            {"name": f"Priya {prefix}nath", "party": "People's Democratic Front"}, 
            {"name": f"Rahul {prefix}das", "party": "Independent"}
        ]}],
    }


def _ensure_api_key() -> None:
    global _API_KEY
    _API_KEY = os.environ.get("GOOGLE_CIVIC_API_KEY")
    if not _API_KEY:
        raise CivicAPIError("GOOGLE_CIVIC_API_KEY not set. Use mock endpoints for dev.")


def _handle_response(resp: httpx.Response) -> None:
    if resp.status_code != 200:
        raise CivicAPIError(f"Civic API {resp.status_code}: {resp.text[:200]}")
