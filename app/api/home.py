"""
Home/Root API endpoints
Service information and welcome endpoints
"""

from fastapi import APIRouter

from app.core.config import config

router = APIRouter()


@router.get("/")
async def root():
    """
    Root endpoint - Service information.
    Returns basic service metadata and status.
    """
    return {
        "service": config.service_name,
        "version": config.service_version,
        "environment": config.environment,
        "message": "Product Service is running",
        "status": "operational"
    }
