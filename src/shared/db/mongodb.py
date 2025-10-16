import os

from motor.motor_asyncio import AsyncIOMotorClient

from src.shared.core.errors import ErrorResponse
from src.shared.core.logger import logger


async def get_db():
    # Construct MongoDB connection string from environment variables
    mongo_host = os.getenv("MONGODB_HOST", "localhost")
    mongo_port = os.getenv("MONGODB_PORT", "27017")
    mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    mongo_database = os.getenv("MONGO_INITDB_DATABASE")
    mongo_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    # Construct MongoDB URI
    if mongo_username and mongo_password:
        MONGODB_URI = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_database}?authSource={mongo_auth_source}"
    else:
        MONGODB_URI = f"mongodb://{mongo_host}:{mongo_port}/{mongo_database}"
    
    MONGODB_DB_NAME = mongo_database or os.getenv("DATABASE_NAME") or os.getenv("MONGODB_DB_NAME")
    
    logger.debug(
        "Attempting to connect to MongoDB",
        metadata={"event": "mongodb_connect_attempt", "uri": f"{mongo_host}:{mongo_port}", "db_name": MONGODB_DB_NAME}
    )
    
    # Validate required environment variables
    if not mongo_host:
        logger.error(
            "MONGODB_HOST must be set in the environment or .env file",
            metadata={"event": "mongodb_env_error"}
        )
        raise RuntimeError(
            "MONGODB_HOST must be set in the environment or .env file"
        )
    
    if not MONGODB_DB_NAME:
        logger.error(
            "DATABASE_NAME or MONGODB_DB_NAME must be set in the environment or .env file",
            metadata={"event": "mongodb_env_error"}
        )
        raise RuntimeError(
            "DATABASE_NAME or MONGODB_DB_NAME must be set in the environment or .env file"
        )
    
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]

    # Test if the database exists by listing its collections
    try:
        collections = await db.list_collection_names()
        logger.info(
            f"Successfully connected to MongoDB database '{MONGODB_DB_NAME}'",
            metadata={"event": "mongodb_connected", "database": MONGODB_DB_NAME, "collections_count": len(collections)}
        )
        if not collections:
            logger.warning(
                f"MongoDB database '{MONGODB_DB_NAME}' has no collections. Collections will be created on first insert.",
                metadata={"event": "mongodb_db_empty"}
            )
    except ErrorResponse:
        # Re-raise our own error responses
        raise
    except Exception as e:
        logger.error(
            f"MongoDB database '{MONGODB_DB_NAME}' is not accessible: {e}",
            metadata={"event": "mongodb_db_missing", "error": str(e)}
        )
        raise ErrorResponse(
            f"MongoDB database '{MONGODB_DB_NAME}' is not accessible: {e}",
            status_code=503
        )

    return db


async def get_product_collection():
    db = await get_db()
    collections = await db.list_collection_names()
    if "products" not in collections:
        logger.warning(
            f"'products' collection does not exist in database '{db.name}'. It will be created on first insert.",
            metadata={"event": "mongodb_collection_missing"}
        )
        # MongoDB will create the collection automatically on first insert
        # Return the collection reference anyway
    return db["products"]
