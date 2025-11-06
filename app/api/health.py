"""
Health and operational API endpoints
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


@router.get("/health/ready")
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


@router.get("/health/live")
def liveness_check(request: Request):
    """Liveness probe - check if the app is running"""
    return {
        "status": "alive",
        "service": config.service_name,
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time,
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
        
        # Ping the database to verify connectivity
        await db.client.admin.command('ping')
        
        # Check if we can access our specific database
        database = db.database if db.database is not None else db.client[config.mongodb_database]
        collections = await database.list_collection_names()
        
        response_time_ms = (time.time() - check_start) * 1000
        
        logger.debug(
            "Database health check passed",
            metadata={
                "response_time_ms": response_time_ms,
                "collections_count": len(collections),
                "database": config.mongodb_database,
                "event": "health_check_database_success"
            }
        )
        
        return {
            "name": "database",
            "status": "healthy",
            "response_time_ms": round(response_time_ms, 2),
            "database": config.mongodb_database,
            "collections_count": len(collections),
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
                "database_url": config.mongodb_host,
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
                
                if response.status == 200:
                    logger.debug(
                        "Dapr sidecar health check passed",
                        metadata={
                            "response_time_ms": response_time_ms,
                            "dapr_port": dapr_http_port,
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
                else:
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