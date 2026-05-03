"""
@module CandidatesRouter
@description FastAPI routes for Google Civic Information API candidate data.
"""
from fastapi import APIRouter, HTTPException
from backend.services.civic_service import get_candidates
from backend.utils.logger import Logger

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@router.get("/{constituency}")
async def get_candidates_route(constituency: str):
    """
    @description Fetches candidates for a given constituency.
    @param constituency: str - Constituency name
    @returns dict - List of candidates with name, party, manifesto
    """
    if not constituency.strip():
        raise HTTPException(status_code=400, detail="Constituency is required.")
    candidates = await get_candidates(constituency)
    return {"success": True, "candidates": candidates, "constituency": constituency}
