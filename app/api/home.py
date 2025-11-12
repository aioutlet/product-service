"""
Home/Root API endpoints
Service information and welcome endpoints
"""

import time
from datetime import datetime

from fastapi import APIRouter, Request

from app.core.config import config

router = APIRouter()

# Track service start time (imported from operational for consistency)
from app.api.operational import start_time


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


@router.get("/version")
def get_version(request: Request):
    """
    Get service version information.
    Used for deployment tracking and version verification.
    """
    return {
        "version": config.service_version,
    }


@router.get("/info")
def get_service_info(request: Request):
    """
    Get comprehensive service information.
    Useful for service discovery and debugging.
    """
    return {
        "service": config.service_name,
        "version": config.service_version,
        "api_version": config.api_version,
        "environment": config.environment,
        "uptime_seconds": round(time.time() - start_time, 2),
        "configuration": {
            "dapr_http_port": config.dapr_http_port,
            "dapr_grpc_port": config.dapr_grpc_port,
            "log_level": config.log_level,
        },
        "timestamp": datetime.now().isoformat(),
    }
