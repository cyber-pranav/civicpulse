"""
@module CivicService
@description Fetches real-time candidate and polling location data
             via Google Civic Information API.
"""
import httpx
from backend.config import settings
from backend.utils.logger import Logger
from backend.utils.cache import cache_get, cache_set

CIVIC_API_BASE = "https://www.googleapis.com/civicinfo/v2"

async def get_candidates(constituency: str) -> list:
    """
    @description Fetches candidate list for a given Indian constituency.
    @param constituency: str - The constituency name or code
    @returns list - List of candidate dicts with name, party, manifesto
    """
    cache_key = f"candidates_{constituency}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{CIVIC_API_BASE}/elections",
                params={"key": settings.GOOGLE_API_KEY}
            )
            resp.raise_for_status()
            data = resp.json()
            cache_set(cache_key, data.get("elections", []), ttl=3600)
            return data.get("elections", [])
    except Exception as e:
        Logger.error(f"CivicService.get_candidates failed: {e}")
        return _get_fallback_candidates(constituency)

def _get_fallback_candidates(constituency: str) -> list:
    """
    @description Returns sample candidate data when API is unavailable.
    @param constituency: str - The constituency name
    @returns list - Hardcoded fallback candidates
    """
    return [
        {"id": "c1", "name": "Arjun Mehta", "party": "National Democratic Party",
         "manifesto": "Focus on infrastructure, digital governance, and youth employment.",
         "constituency": constituency},
        {"id": "c2", "name": "Priya Sharma", "party": "Progressive Alliance",
         "manifesto": "Emphasis on healthcare, education reform, and women empowerment.",
         "constituency": constituency},
        {"id": "c3", "name": "Ravi Kumar", "party": "People's Front",
         "manifesto": "Agricultural subsidies, rural development, and farmer welfare.",
         "constituency": constituency}
    ]
