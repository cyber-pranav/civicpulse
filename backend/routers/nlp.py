"""
@module NLPRouter
@description FastAPI routes for Google Cloud Natural Language API features.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.nlp_service import analyze_sentiment
from backend.utils.logger import Logger

router = APIRouter(prefix="/api/nlp", tags=["NLP"])

class SentimentRequest(BaseModel):
    text: str

@router.post("/sentiment")
async def sentiment_route(req: SentimentRequest):
    """
    @description Analyses sentiment of manifesto text.
    @returns dict - score, magnitude, label
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")
    result = await analyze_sentiment(req.text)
    return {"success": True, "data": result}
