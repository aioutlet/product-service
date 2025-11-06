"""
Operational and monitoring API endpoints
Provides metrics, version info, and other operational endpoints
"""

import os
import time
import psutil
from datetime import datetime

from fastapi import APIRouter, Request

from app.core.config import config
from app.core.logger import logger

router = APIRouter()

# Track service start time
start_time = time.time()


@router.get("/metrics")
def get_metrics(request: Request):
    """
    Get service metrics for monitoring.
    Used by Prometheus, monitoring tools, or APM systems.
    """
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get system-level metrics
        system_memory = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        
        logger.debug(
            "Metrics endpoint called",
            metadata={
                "event": "metrics_requested",
                "memory_percent": system_memory.percent
            }
        )
        
        return {
            "service": config.service_name,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(time.time() - start_time, 2),
            "process": {
                "pid": os.getpid(),
                "memory_rss_bytes": memory_info.rss,
                "memory_vms_bytes": memory_info.vms,
                "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(),
            },
            "system": {
                "memory_total_bytes": system_memory.total,
                "memory_available_bytes": system_memory.available,
                "memory_used_percent": round(system_memory.percent, 2),
                "disk_total_bytes": disk_usage.total,
                "disk_used_bytes": disk_usage.used,
                "disk_used_percent": round(disk_usage.percent, 2),
            },
            "runtime": {
                "python_version": os.sys.version.split()[0],
                "platform": os.sys.platform,
            }
        }
    except Exception as e:
        logger.error(
            f"Failed to get metrics: {str(e)}",
            metadata={"event": "metrics_error", "error": str(e)}
        )
        return {
            "service": config.service_name,
            "timestamp": datetime.now().isoformat(),
            "error": "Failed to retrieve metrics",
            "details": str(e)
        }


@router.get("/version")
def get_version(request: Request):
    """
    Get service version information.
    Used for deployment tracking and version verification.
    """
    logger.debug(
        "Version endpoint called",
        metadata={"event": "version_requested"}
    )
    
    return {
        "service": config.service_name,
        "version": config.service_version,
        "api_version": config.api_version,
        "environment": config.environment,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/info")
def get_service_info(request: Request):
    """
    Get comprehensive service information.
    Useful for service discovery and debugging.
    """
    logger.debug(
        "Info endpoint called",
        metadata={"event": "info_requested"}
    )
    
    return {
        "service": config.service_name,
        "version": config.service_version,
        "api_version": config.api_version,
        "environment": config.environment,
        "uptime_seconds": round(time.time() - start_time, 2),
        "configuration": {
            "mongodb_host": config.mongodb_host,
            "mongodb_port": config.mongodb_port,
            "mongodb_database": config.mongodb_database,
            "dapr_http_port": config.dapr_http_port,
            "dapr_grpc_port": config.dapr_grpc_port,
            "log_level": config.log_level,
        },
        "timestamp": datetime.now().isoformat(),
    }
