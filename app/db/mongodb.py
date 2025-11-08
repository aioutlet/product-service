"""
MongoDB database connection and configuration following FastAPI best practices
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.core.config import config
from app.core.errors import ErrorResponse
from app.core.logger import logger
from app.services.dapr_secret_manager import get_database_config


class Database:
    """Database connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    database = None


db = Database()


async def connect_to_mongo():
    """Create database connection"""
    logger.info("Connecting to MongoDB...")
    
    try:
        # Get database configuration from Dapr Secret Manager (not async)
        db_config = get_database_config()
        
        # Build MongoDB URL
        username = db_config.get('username', '')
        password = db_config.get('password', '')
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', '27019')
        database = db_config.get('database', 'productdb')
        
        if username and password:
            mongodb_url = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
        else:
            mongodb_url = f"mongodb://{host}:{port}/{database}"
        
        db.client = AsyncIOMotorClient(mongodb_url)
        db.database = db.client[database]
        
        # Test connection
        await db.client.admin.command('ping')
        
        logger.info(
            f"Successfully connected to MongoDB database '{database}'",
            metadata={
                "event": "mongodb_connected", 
                "database": database,
                "host": host,
                "port": port
            }
        )
    except Exception as e:
        logger.error(
            f"Could not connect to MongoDB: {e}",
            metadata={"event": "mongodb_connection_error", "error": str(e)}
        )
        raise ErrorResponse(
            f"Could not connect to MongoDB: {e}",
            status_code=503
        )


async def close_mongo_connection():
    """Close database connection"""
    logger.info("Closing connection to MongoDB...")
    if db.client is not None:
        db.client.close()


async def get_database():
    """Get database instance"""
    if db.database is None:
        await connect_to_mongo()
    return db.database


async def get_product_collection():
    """Get products collection"""
    database = await get_database()
    return database["products"]