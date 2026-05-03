"""
@module TranslateRouter
@description FastAPI routes for Google Cloud Translation API.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.translate_service import translate_text, SUPPORTED_LANGUAGES

router = APIRouter(prefix="/api/translate", tags=["Translation"])

class TranslateRequest(BaseModel):
    text: str
    target_language: str

@router.post("/")
async def translate_route(req: TranslateRequest):
    """
    @description Translates a text string to target language.
    @returns dict - translated string
    """
    if req.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported: {list(SUPPORTED_LANGUAGES.keys())}"
        )
    translated = await translate_text(req.text, req.target_language)
    return {"success": True, "translated": translated, "language": req.target_language}

@router.get("/languages")
async def get_languages():
    """
    @description Returns all supported language codes and names.
    @returns dict - language code to name mapping
    """
    return {"success": True, "languages": SUPPORTED_LANGUAGES}
