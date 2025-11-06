"""
MongoDB database connection and configuration following FastAPI best practices
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.core.config import config
from app.core.errors import ErrorResponse
from app.core.logger import logger


class Database:
    """Database connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    database = None


db = Database()


async def connect_to_mongo():
    """Create database connection"""
    logger.info("Connecting to MongoDB...")
    
    try:
        db.client = AsyncIOMotorClient(config.mongodb_url)
        db.database = db.client[config.mongodb_database]
        
        # Test connection
        await db.client.admin.command('ping')
        
        logger.info(
            f"Successfully connected to MongoDB database '{config.mongodb_database}'",
            metadata={
                "event": "mongodb_connected", 
                "database": config.mongodb_database,
                "host": config.mongodb_host,
                "port": config.mongodb_port
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
    if db.client:
        db.client.close()


async def get_database():
    """Get database instance"""
    if not db.database:
        await connect_to_mongo()
    return db.database


async def get_product_collection():
    """Get products collection"""
    database = await get_database()
    return database["products"]