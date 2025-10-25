"""
Dependency Health Checker
Checks the health of external service dependencies at startup
Logs health status but does not block application startup
"""

import asyncio
import os
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorClient


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

        print(f'[DB] Checking database health at {mongo_host}:{mongo_port}')

        # Create MongoDB connection URI
        if mongo_username and mongo_password:
            mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_database}?authSource={mongo_auth_source}"
            # Hide password in logs
            safe_uri = mongo_uri.replace(f':{mongo_password}@', ':***@')
            print(f'[DB] Using MongoDB URI: {safe_uri}')
        else:
            mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/{mongo_database}"
            print(f'[DB] Using MongoDB URI: {mongo_uri}')

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

        print('[DB] ✅ Database connection is healthy')
        client.close()
        return {'service': 'database', 'status': 'healthy'}

    except asyncio.TimeoutError:
        print('[DB] ❌ Database health check timed out')
        return {'service': 'database', 'status': 'timeout', 'error': 'Connection timeout'}
    except Exception as error:
        print(f'[DB] ❌ Database health check failed: {str(error)}')
        return {'service': 'database', 'status': 'unhealthy', 'error': str(error)}


async def check_service_health(service_name: str, health_url: str, timeout: int = 5) -> dict:
    """
    Check health of an external service via HTTP
    """
    try:
        import aiohttp
        
        print(f'[DEPS] Checking {service_name} health at {health_url}')

        async with aiohttp.ClientSession() as session:
            async with session.get(
                health_url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={'Accept': 'application/json'}
            ) as response:
                if response.status == 200:
                    print(f'[DEPS] ✅ {service_name} is healthy')
                    return {'service': service_name, 'status': 'healthy', 'url': health_url}
                else:
                    print(f'[DEPS] ⚠️ {service_name} returned status {response.status}')
                    return {
                        'service': service_name,
                        'status': 'unhealthy',
                        'url': health_url,
                        'statusCode': response.status
                    }

    except asyncio.TimeoutError:
        print(f'[DEPS] ⏰ {service_name} health check timed out after {timeout}s')
        return {'service': service_name, 'status': 'timeout', 'error': 'timeout'}
    except Exception as error:
        print(f'[DEPS] ❌ {service_name} is not reachable: {str(error)}')
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
    print('[DEPS] 🔍 Checking dependency health...')

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
        print(f'[DEPS] 🎉 All {total_services} dependencies are healthy')
    else:
        print(f'[DEPS] ⚠️ {healthy_services}/{total_services} dependencies are healthy')

    return health_checks


def get_dependencies() -> Dict[str, str]:
    """
    Get dependency URLs from environment variables
    Uses standardized _HEALTH_URL variables for complete health endpoint URLs
    
    Returns:
        Dict with service names as keys and health URLs as values
    """
    dependencies = {}

    # Add message broker if configured (primary dependency for product-service)
    message_broker_health_url = os.getenv('MESSAGE_BROKER_HEALTH_URL')
    if message_broker_health_url:
        dependencies['message-broker'] = message_broker_health_url

    return dependencies
