from fastapi import APIRouter
from backend.config import settings

router = APIRouter(prefix="/api/config", tags=["Config"])

@router.get("/")
async def get_config():
    """
    @description Gets public configuration.
    @returns dict - Configuration values
    """
    return {"maps_key": settings.MAPS_API_KEY}
