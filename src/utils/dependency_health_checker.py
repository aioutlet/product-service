"""
Dependency Health Checker
Checks the health of business dependencies at startup
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


async def check_dependency_health() -> List[dict]:
    """
    Check health of business dependencies without blocking startup
    Currently only checks database - the primary business dependency
    
    Returns:
        List of health check results
    """
    logger.info(
        "Starting dependency health checks",
        metadata={"operation": "health_check"}
    )

    # Check database health - our primary business dependency
    health_checks = [await check_database_health()]

    # Summary logging
    healthy_services = sum(1 for check in health_checks if check.get('status') == 'healthy')
    total_services = len(health_checks)

    if healthy_services == total_services:
        logger.info(
            "All dependencies are healthy",
            metadata={
                "operation": "health_check",
                "healthy_count": healthy_services,
                "total_count": total_services,
                "status": "all_healthy"
            }
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
