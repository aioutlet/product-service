"""
Operational/Infrastructure endpoints
These endpoints are used by monitoring systems, load balancers, and DevOps tools
"""

import os
import time
import psutil
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from src.core.logger import logger

start_time = time.time()

def health(request: Request):
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "product-service",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("API_VERSION", "1.0.0")
    }

def readiness(request: Request):
    """Readiness probe - check if service is ready to serve traffic"""
    try:
        # Add more sophisticated checks here (DB connectivity, external dependencies, etc.)
        # Example: Check database connectivity, external APIs, etc.
        # await check_database_connection()
        # await check_external_api_connectivity()
        
        return {
            "status": "ready",
            "service": "product-service",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "connected",
                "external_apis": "connected",
                # Add other dependency checks
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "service": "product-service",
                "timestamp": datetime.now().isoformat(),
                "error": "Service dependencies not available"
            }
        )

def liveness(request: Request):
    """Liveness probe - check if the app is running"""
    return {
        "status": "alive",
        "service": "product-service",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time
    }

def metrics(request: Request):
    """Basic metrics endpoint"""
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
