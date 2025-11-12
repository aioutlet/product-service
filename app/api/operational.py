"""
Operational and monitoring API endpoints
Provides health checks, metrics, and other operational endpoints
"""

import os
import time
import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any, List

import aiohttp
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import config
from app.core.logger import logger
from app.db.mongodb import db

router = APIRouter()

# Track service start time
start_time = time.time()


@router.get("/health")
def health_check(request: Request):
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": config.service_name,
        "timestamp": datetime.now().isoformat(),
        "version": config.api_version,
    }


@router.get("/readiness")
async def readiness_check(request: Request):
    """Readiness probe - check if service is ready to serve traffic"""
    try:
        # Perform comprehensive health checks
        health_checks = await perform_health_checks()
        
        # Determine overall health status
        failed_checks = [check for check in health_checks if check["status"] != "healthy"]
        
        if not failed_checks:
            return {
                "status": "ready",
                "service": config.service_name,
                "timestamp": datetime.now().isoformat(),
                "checks": health_checks,
            }
        else:
            logger.warning(
                f"Readiness check failed - {len(failed_checks)} checks failed",
                metadata={
                    "failed_checks": [check["name"] for check in failed_checks],
                    "event": "readiness_check_failed"
                }
            )
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not ready",
                    "service": config.service_name,
                    "timestamp": datetime.now().isoformat(),
                    "checks": health_checks,
                    "errors": [f"{check['name']}: {check.get('error', 'Unknown error')}" for check in failed_checks],
                },
            )
    except Exception as e:
        logger.error(f"Readiness check failed with exception: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "service": config.service_name,
                "timestamp": datetime.now().isoformat(),
                "error": f"Health check system failure: {str(e)}",
            },
        )


@router.get("/liveness")
def liveness_check(request: Request):
    """Liveness probe - check if the app is running"""
    return {
        "status": "alive",
        "service": config.service_name,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2),
    }


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


async def perform_health_checks() -> List[Dict[str, Any]]:
    """Perform comprehensive health checks for all dependencies"""
    checks = []
    
    # Run health checks concurrently for better performance
    check_tasks = [
        check_database_health(),
        check_dapr_sidecar_health(),
        check_message_broker_health(),
        check_system_resources(),
    ]
    
    # Wait for all checks to complete
    check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
    
    for result in check_results:
        if isinstance(result, Exception):
            checks.append({
                "name": "unknown_check",
                "status": "unhealthy",
                "error": str(result),
                "timestamp": datetime.now().isoformat(),
            })
        else:
            checks.append(result)
    
    return checks


async def check_database_health() -> Dict[str, Any]:
    """Check MongoDB database connectivity"""
    check_start = time.time()
    
    try:
        if not db.client:
            # Try to establish connection if not already connected
            from app.db.mongodb import connect_to_mongo
            await connect_to_mongo()
        
        # Use ping command which works without listing collections
        # This is sufficient to verify database connectivity
        database = db.database
        await database.command('ping')
        
        response_time_ms = (time.time() - check_start) * 1000
        
        logger.debug(
            "Database health check passed",
            metadata={
                "response_time_ms": response_time_ms,
                "event": "health_check_database_success"
            }
        )
        
        return {
            "name": "database",
            "status": "healthy",
            "response_time_ms": round(response_time_ms, 2),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        response_time_ms = (time.time() - check_start) * 1000
        error_msg = str(e)
        
        logger.error(
            f"Database health check failed: {error_msg}",
            metadata={
                "response_time_ms": response_time_ms,
                "error": error_msg,
                "event": "health_check_database_failed"
            }
        )
        
        return {
            "name": "database",
            "status": "unhealthy",
            "error": error_msg,
            "response_time_ms": round(response_time_ms, 2),
            "timestamp": datetime.now().isoformat(),
        }


async def check_dapr_sidecar_health() -> Dict[str, Any]:
    """Check Dapr sidecar health and connectivity"""
    check_start = time.time()
    dapr_http_port = config.dapr_http_port
    health_url = f"http://localhost:{dapr_http_port}/v1.0/healthz"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                health_url,
                timeout=aiohttp.ClientTimeout(total=3.0),
                headers={'Accept': 'application/json'}
            ) as response:
                response_time_ms = (time.time() - check_start) * 1000
                
                # Dapr health endpoint returns 204 No Content when healthy
                # For local development, accept 500 if it's only placement service warning
                # (we don't use actors in local dev)
                if response.status in (200, 204):
                    logger.debug(
                        "Dapr sidecar health check passed",
                        metadata={
                            "response_time_ms": response_time_ms,
                            "dapr_port": dapr_http_port,
                            "http_status": response.status,
                            "event": "health_check_dapr_success"
                        }
                    )
                    
                    return {
                        "name": "dapr_sidecar",
                        "status": "healthy",
                        "response_time_ms": round(response_time_ms, 2),
                        "dapr_http_port": dapr_http_port,
                        "url": health_url,
                        "timestamp": datetime.now().isoformat(),
                    }
                elif response.status == 500:
                    # Check if it's just placement service (actors) - not critical for pub/sub
                    try:
                        error_data = await response.json()
                        error_msg = error_data.get("message", "")
                        if "placement" in error_msg.lower():
                            # Placement service not ready, but pub/sub still works
                            logger.debug(
                                "Dapr placement service not ready (expected in local dev without actors)",
                                metadata={
                                    "response_time_ms": response_time_ms,
                                    "dapr_port": dapr_http_port,
                                    "event": "health_check_dapr_placement_warning"
                                }
                            )
                            return {
                                "name": "dapr_sidecar",
                                "status": "healthy",
                                "response_time_ms": round(response_time_ms, 2),
                                "dapr_http_port": dapr_http_port,
                                "warning": "Placement service not ready (actors unavailable)",
                                "timestamp": datetime.now().isoformat(),
                            }
                    except:
                        pass
                    
                    error_msg = f"Dapr returned HTTP {response.status}"
                    return {
                        "name": "dapr_sidecar",
                        "status": "unhealthy",
                        "error": error_msg,
                        "response_time_ms": round(response_time_ms, 2),
                        "http_status": response.status,
                        "timestamp": datetime.now().isoformat(),
                    }
                    
    except asyncio.TimeoutError:
        response_time_ms = (time.time() - check_start) * 1000
        error_msg = "Dapr sidecar connection timeout"
        
        logger.warning(
            error_msg,
            metadata={
                "response_time_ms": response_time_ms,
                "dapr_port": dapr_http_port,
                "event": "health_check_dapr_timeout"
            }
        )
        
        return {
            "name": "dapr_sidecar",
            "status": "unhealthy",
            "error": error_msg,
            "response_time_ms": round(response_time_ms, 2),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        response_time_ms = (time.time() - check_start) * 1000
        error_msg = f"Dapr sidecar check failed: {str(e)}"
        
        logger.error(
            error_msg,
            metadata={
                "response_time_ms": response_time_ms,
                "dapr_port": dapr_http_port,
                "error": str(e),
                "event": "health_check_dapr_failed"
            }
        )
        
        return {
            "name": "dapr_sidecar",
            "status": "unhealthy", 
            "error": error_msg,
            "response_time_ms": round(response_time_ms, 2),
            "timestamp": datetime.now().isoformat(),
        }


async def check_message_broker_health() -> Dict[str, Any]:
    """Check message broker (RabbitMQ) connectivity via Dapr pub/sub"""
    check_start = time.time()
    dapr_http_port = config.dapr_http_port
    pubsub_name = "product-pubsub"  # Default pubsub component name
    
    # Test pub/sub connectivity by attempting to get component metadata
    metadata_url = f"http://localhost:{dapr_http_port}/v1.0/metadata"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                metadata_url,
                timeout=aiohttp.ClientTimeout(total=3.0),
                headers={'Accept': 'application/json'}
            ) as response:
                response_time_ms = (time.time() - check_start) * 1000
                
                if response.status == 200:
                    metadata = await response.json()
                    components = metadata.get('components', [])
                    pubsub_components = [
                        c for c in components 
                        if c.get('type', '').startswith('pubsub.')
                    ]
                    
                    if pubsub_components:
                        logger.debug(
                            "Message broker health check passed",
                            metadata={
                                "response_time_ms": response_time_ms,
                                "pubsub_components": len(pubsub_components),
                                "event": "health_check_pubsub_success"
                            }
                        )
                        
                        return {
                            "name": "message_broker",
                            "status": "healthy",
                            "response_time_ms": round(response_time_ms, 2),
                            "pubsub_components": len(pubsub_components),
                            "components": [c.get('name') for c in pubsub_components],
                            "timestamp": datetime.now().isoformat(),
                        }
                    else:
                        return {
                            "name": "message_broker",
                            "status": "unhealthy",
                            "error": "No pub/sub components found in Dapr",
                            "response_time_ms": round(response_time_ms, 2),
                            "timestamp": datetime.now().isoformat(),
                        }
                else:
                    error_msg = f"Dapr metadata endpoint returned HTTP {response.status}"
                    return {
                        "name": "message_broker",
                        "status": "unhealthy",
                        "error": error_msg,
                        "response_time_ms": round(response_time_ms, 2),
                        "timestamp": datetime.now().isoformat(),
                    }
                    
    except Exception as e:
        response_time_ms = (time.time() - check_start) * 1000
        error_msg = f"Message broker check failed: {str(e)}"
        
        logger.warning(
            error_msg,
            metadata={
                "response_time_ms": response_time_ms,
                "error": str(e),
                "event": "health_check_pubsub_failed"
            }
        )
        
        return {
            "name": "message_broker",
            "status": "degraded",  # Non-critical for basic operations
            "error": error_msg,
            "response_time_ms": round(response_time_ms, 2),
            "timestamp": datetime.now().isoformat(),
        }


async def check_system_resources() -> Dict[str, Any]:
    """Check system resources (memory, CPU, disk space)"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        # Get system memory information
        system_memory = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        
        # Define thresholds
        memory_threshold_percent = 90
        disk_threshold_percent = 85
        cpu_threshold_percent = 95
        
        # Check if any thresholds are exceeded
        warnings = []
        if system_memory.percent > memory_threshold_percent:
            warnings.append(f"High system memory usage: {system_memory.percent:.1f}%")
        
        if disk_usage.percent > disk_threshold_percent:
            warnings.append(f"High disk usage: {disk_usage.percent:.1f}%")
        
        if cpu_percent > cpu_threshold_percent:
            warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        status = "healthy" if not warnings else "degraded"
        
        result = {
            "name": "system_resources",
            "status": status,
            "metrics": {
                "process_memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                "process_cpu_percent": round(cpu_percent, 2),
                "system_memory_percent": round(system_memory.percent, 2),
                "disk_usage_percent": round(disk_usage.percent, 2),
                "uptime_seconds": round(time.time() - start_time, 2),
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        if warnings:
            result["warnings"] = warnings
        
        logger.debug(
            "System resources health check completed",
            metadata={
                "status": status,
                "warnings_count": len(warnings),
                "memory_percent": system_memory.percent,
                "event": "health_check_resources_completed"
            }
        )
        
        return result
        
    except Exception as e:
        error_msg = f"System resources check failed: {str(e)}"
        
        logger.error(
            error_msg,
            metadata={
                "error": str(e),
                "event": "health_check_resources_failed"
            }
        )
        
        return {
            "name": "system_resources",
            "status": "unhealthy",
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
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
            "dapr_http_port": config.dapr_http_port,
            "dapr_grpc_port": config.dapr_grpc_port,
            "log_level": config.log_level,
        },
        "timestamp": datetime.now().isoformat(),
    }
