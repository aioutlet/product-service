"""
Health check and monitoring endpoints.
"""

import os
import time
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
import psutil

from src.dependencies import get_database
from src.core.logger import logger

router = APIRouter(tags=["health"])

# Track service start time for uptime calculations
start_time = time.time()


@router.get("/health")
async def health_check():
    """Liveness probe - service is running."""
    return {
        "status": "healthy",
        "service": "product-service",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("API_VERSION", "1.0.0"),
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Readiness probe - service is ready to accept traffic.
    
    Checks database connectivity.
    """
    try:
        await db.command("ping")
        return {
            "status": "ready",
            "service": "product-service",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "product-service",
                "timestamp": datetime.now().isoformat(),
                "database": "disconnected",
                "error": str(e)
            }
        )


@router.get("/health/live")
async def liveness_check():
    """Alternative liveness endpoint."""
    return {
        "status": "alive",
        "service": "product-service",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time
    }


@router.get("/metrics")
async def metrics():
    """Basic metrics endpoint for monitoring."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "service": "product-service",
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "uptime": time.time() - start_time,
            "memory": {
                "rss": memory_info.rss,
                "vms": memory_info.vms
            },
            "cpu_percent": process.cpu_percent(),
            "pid": os.getpid(),
            "python_version": os.sys.version
        }
    }
