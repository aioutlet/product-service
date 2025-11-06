"""
Dependency Health Checker
Checks the health of external service dependencies at startup
Logs health status but does not block application startup
"""

import asyncio
import os
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.logger import logger


async def check_database_health() -> dict:
    """
    Check MongoDB database health using independent connection
    Returns database health status
    """
    try:
        mongo_host = os.getenv('MONGODB_HOST', 'localhost')
        mongo_port = os.getenv('MONGODB_PORT', '27017')
        mongo_username = os.getenv('MONGO_INITDB_ROOT_USERNAME')
        mongo_password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
        mongo_database = os.getenv('MONGO_INITDB_DATABASE')
        mongo_auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')

        logger.info(
            "Checking database health",
            metadata={
                "operation": "health_check",
                "database_host": mongo_host,
                "database_port": mongo_port
            }
        )

        # Create MongoDB connection URI
        if mongo_username and mongo_password:
            mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_database}?authSource={mongo_auth_source}"
            # Hide password in logs
            safe_uri = mongo_uri.replace(f':{mongo_password}@', ':***@')
            logger.debug(
                "Using MongoDB URI with authentication",
                metadata={
                    "operation": "health_check", 
                    "uri": safe_uri
                }
            )
        else:
            mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/{mongo_database}"
            logger.debug(
                "Using MongoDB URI without authentication",
                metadata={
                    "operation": "health_check",
                    "uri": mongo_uri
                }
            )

        # Create a separate client for health checking with timeout
        client = AsyncIOMotorClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=5000,
            connectTimeoutMS=5000,
        )

        # Attempt to ping the database
        await asyncio.wait_for(
            client.admin.command('ping'),
            timeout=6.0
        )

        logger.info(
            "Database connection is healthy",
            metadata={
                "operation": "health_check",
                "status": "healthy"
            }
        )
        client.close()
        return {'service': 'database', 'status': 'healthy'}

    except asyncio.TimeoutError:
        logger.error(
            "Database health check timed out",
            metadata={
                "operation": "health_check",
                "status": "timeout"
            }
        )
        return {'service': 'database', 'status': 'timeout', 'error': 'Connection timeout'}
    except Exception as error:
        logger.error(
            "Database health check failed",
            metadata={
                "operation": "health_check",
                "status": "unhealthy",
                "error": str(error)
            }
        )
        return {'service': 'database', 'status': 'unhealthy', 'error': str(error)}


async def check_service_health(service_name: str, health_url: str, timeout: int = 5) -> dict:
    """
    Check health of an external service via HTTP
    """
    try:
        import aiohttp
        
        logger.info(
            "Checking external service health",
            metadata={
                "operation": "health_check",
                "service": service_name,
                "url": health_url
            }
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                health_url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={'Accept': 'application/json'}
            ) as response:
                if response.status == 200:
                    logger.info(
                        "External service is healthy",
                        operation="health_check",
                        service=service_name,
                        status="healthy"
                    )
                    return {'service': service_name, 'status': 'healthy', 'url': health_url}
                else:
                    logger.warning(
                        "External service returned non-200 status",
                        metadata={
                            "operation": "health_check",
                            "service": service_name,
                            "status": "unhealthy",
                            "status_code": response.status
                        }
                    )
                    return {
                        'service': service_name,
                        'status': 'unhealthy',
                        'url': health_url,
                        'statusCode': response.status
                    }

    except asyncio.TimeoutError:
        logger.warning(
            "External service health check timed out",
            metadata={
                "operation": "health_check",
                "service": service_name,
                "status": "timeout",
                "timeout_seconds": timeout
            }
        )
        return {'service': service_name, 'status': 'timeout', 'error': 'timeout'}
    except Exception as error:
        logger.error(
            "External service is not reachable",
            metadata={
                "operation": "health_check",
                "service": service_name,
                "status": "unreachable",
                "error": str(error)
            }
        )
        return {'service': service_name, 'status': 'unreachable', 'error': str(error)}


async def check_dependency_health(dependencies: Dict[str, str], timeout: int = 5) -> List[dict]:
    """
    Check health of service dependencies without blocking startup
    
    Args:
        dependencies: Dict with service names as keys and health URLs as values
        timeout: Timeout for each health check in seconds
    
    Returns:
        List of health check results
    """
    logger.info(
        "Starting dependency health checks",
        metadata={
            "operation": "health_check",
            "dependency_count": len(dependencies)
        }
    )

    # Check database health first
    db_health = await check_database_health()
    health_checks = [db_health]

    # Add external service health checks
    for service_name, health_url in dependencies.items():
        result = await check_service_health(service_name, health_url, timeout)
        health_checks.append(result)

    # Summary logging
    healthy_services = sum(1 for check in health_checks if check.get('status') == 'healthy')
    total_services = len(health_checks)

    if healthy_services == total_services:
        logger.info(
            "All dependencies are healthy",
            operation="health_check",
            healthy_count=healthy_services,
            total_count=total_services,
            status="all_healthy"
        )
    else:
        logger.warning(
            "Some dependencies are unhealthy",
            metadata={
                "operation": "health_check",
                "healthy_count": healthy_services,
                "total_count": total_services,
                "status": "partial_healthy"
            }
        )

    return health_checks


def get_dependencies() -> Dict[str, str]:
    """
    Get dependency URLs from environment variables
    Uses standardized _HEALTH_URL variables for complete health endpoint URLs
    
    Returns:
        Dict with service names as keys and health URLs as values
    """
    dependencies = {}

    # Add Dapr sidecar health check only if running with Dapr
    # Check if we're running in Dapr mode by looking for DAPR_HTTP_PORT in environment
    dapr_port = os.getenv('DAPR_HTTP_PORT')
    if dapr_port:
        # In Kubernetes/AKS, Dapr sidecar is always on localhost (same pod)
        # In development, it's also localhost
        # Allow override via DAPR_HOST for special cases (e.g., Docker Compose)
        dapr_host = os.getenv('DAPR_HOST', 'localhost')
        dapr_health_url = f"http://{dapr_host}:{dapr_port}/v1.0/healthz"
        dependencies['dapr-sidecar'] = dapr_health_url

    # Add other services via Dapr (these will be checked when Dapr is available)
    # The actual service health can be checked via Dapr service invocation
    # dependencies['user-service-via-dapr'] = f"http://localhost:{dapr_port}/v1.0/invoke/user-service/method/health"
    # dependencies['inventory-service-via-dapr'] = f"http://localhost:{dapr_port}/v1.0/invoke/inventory-service/method/health"

    return dependencies
