"""
@module AIRouter
@description FastAPI routes for Gemini AI features:
             candidate analysis, civic Q&A, and intelligent search.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.gemini_service import (
    analyze_candidate, answer_civic_question, search_candidates
)

router = APIRouter(prefix="/api/ai", tags=["AI"])

class CandidateAnalysisRequest(BaseModel):
    candidate_name: str
    manifesto: str

class ChatRequest(BaseModel):
    question: str
    history: list = []

class SearchRequest(BaseModel):
    query: str
    candidates: list

@router.post("/analyze-candidate")
async def analyze_candidate_route(req: CandidateAnalysisRequest):
    """
    @description Analyzes a candidate manifesto with Gemini AI.
    @returns dict - tone, topTopics, voterAppeal, redFlags
    """
    if not req.manifesto.strip():
        raise HTTPException(status_code=400, detail="Manifesto text is required.")
    result = await analyze_candidate(req.candidate_name, req.manifesto)
    return {"success": True, "data": result}

@router.post("/chat")
async def civic_chat_route(req: ChatRequest):
    """
    @description Answers a civic/election question via Gemini.
    @returns dict - answer string
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    answer = await answer_civic_question(req.question, req.history)
    return {"success": True, "answer": answer}

@router.post("/search")
async def search_candidates_route(req: SearchRequest):
    """
    @description Intelligent candidate search powered by Gemini.
    @returns dict - list of matching candidate IDs
    """
    if not req.query.strip():
        return {"success": True, "ids": [c["id"] for c in req.candidates]}
    ids = await search_candidates(req.query, req.candidates)
    return {"success": True, "ids": ids}
