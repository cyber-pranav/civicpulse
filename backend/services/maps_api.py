"""
maps_api.py — Google Maps API Service Wrapper.

Calculates "Time to Booth" and generates deep-link URLs for directions.
Zero-PII: addresses used only in-flight, never stored.
"""

from __future__ import annotations
import os
import urllib.parse
from typing import Any, Optional
import httpx

MAPS_API_BASE = "https://maps.googleapis.com/maps/api"
_API_KEY: Optional[str] = os.environ.get("GOOGLE_MAPS_API_KEY")
REQUEST_TIMEOUT: float = 10.0


class MapsAPIError(Exception):
    """Raised on Google Maps API errors."""


async def get_time_to_booth(origin: str, destination: str) -> dict[str, Any]:
    """
    Calculate travel time from user's location to polling booth.

    Uses the Distance Matrix API.

    Returns dict with distance_text, duration_text, duration_seconds.
    """
    _ensure_api_key()
    params = {
        "key": _API_KEY,
        "origins": origin,
        "destinations": destination,
        "mode": "driving",
        "language": "en",
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(f"{MAPS_API_BASE}/distancematrix/json", params=params)
        if resp.status_code != 200:
            raise MapsAPIError(f"Maps API {resp.status_code}")
        data = resp.json()

    rows = data.get("rows", [])
    if not rows or not rows[0].get("elements"):
        raise MapsAPIError("No route found.")

    element = rows[0]["elements"][0]
    if element.get("status") != "OK":
        raise MapsAPIError(f"Route status: {element.get('status')}")

    return {
        "distance_text": element["distance"]["text"],
        "duration_text": element["duration"]["text"],
        "duration_seconds": element["duration"]["value"],
    }


def generate_directions_url(origin: str, destination: str) -> str:
    """
    Generate a Google Maps deep-link URL for booth directions.

    Works on both mobile (opens Google Maps app) and desktop (web).

    Parameters
    ----------
    origin : str
        Starting location or coordinates.
    destination : str
        Polling booth address.

    Returns
    -------
    str
        Google Maps directions URL.
    """
    params = urllib.parse.urlencode({
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": "driving",
    })
    return f"https://www.google.com/maps/dir/?{params}"


def get_mock_time_to_booth(origin: str, destination: str) -> dict[str, Any]:
    """Mock travel time for demos without an API key."""
    return {
        "origin": origin,
        "destination": destination,
        "distance_text": "4.2 km",
        "duration_text": "12 mins",
        "duration_seconds": 720,
        "directions_url": generate_directions_url(origin, destination),
    }


def _ensure_api_key() -> None:
    global _API_KEY
    _API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not _API_KEY:
        raise MapsAPIError("GOOGLE_MAPS_API_KEY not set. Use mock endpoints for dev.")
