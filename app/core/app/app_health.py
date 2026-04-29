from fastapi import APIRouter

# from fastapi.responses import JSONResponse  # type: ignore
from app.core.config.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
    }
