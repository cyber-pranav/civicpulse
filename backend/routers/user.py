"""
@module UserRouter
@description FastAPI routes for Firebase Auth and Firestore user progress.
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from backend.services.firebase_service import (
    save_user_progress, load_user_progress, verify_token
)
from backend.utils.logger import Logger

router = APIRouter(prefix="/api/user", tags=["User"])

class ProgressRequest(BaseModel):
    progress: dict

async def _get_verified_uid(authorization: str | None) -> str:
    """
    @description Extracts and verifies Firebase Auth token from header.
    @param authorization: str - Bearer token header value
    @returns str - Verified user ID
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split("Bearer ")[1]
    decoded = await verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return decoded["uid"]

@router.get("/progress")
async def get_progress(authorization: str | None = Header(default=None)):
    """
    @description Loads user journey progress from Firestore.
    @returns dict - Saved progress state
    """
    uid = await _get_verified_uid(authorization)
    progress = await load_user_progress(uid)
    return {"success": True, "progress": progress}

@router.post("/progress")
async def save_progress(
    req: ProgressRequest,
    authorization: str | None = Header(default=None)
):
    """
    @description Saves user journey progress to Firestore.
    @returns dict - Success status
    """
    uid = await _get_verified_uid(authorization)
    saved = await save_user_progress(uid, req.progress)
    return {"success": saved}
