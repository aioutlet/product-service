import os

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.services.dapr_secret_manager import get_database_config


async def get_db():
    # Get database configuration from Dapr secret manager
    try:
        db_config = get_database_config()
    except Exception as e:
        logger.warning(f"Failed to get database config from Dapr secrets, falling back to environment variables: {e}")
        # Fallback to environment variables
        db_config = {
            'host': os.getenv("MONGODB_HOST", "localhost"),
            'port': int(os.getenv("MONGODB_PORT", "27017")),
            'username': os.getenv("MONGO_INITDB_ROOT_USERNAME"),
            'password': os.getenv("MONGO_INITDB_ROOT_PASSWORD"),
            'database': os.getenv("MONGO_INITDB_DATABASE"),
            'auth_source': os.getenv("MONGODB_AUTH_SOURCE", "admin")
        }
    
    # Construct MongoDB URI
    if db_config['username'] and db_config['password']:
        MONGODB_URI = f"mongodb://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?authSource={db_config['auth_source']}"
    else:
        MONGODB_URI = f"mongodb://{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    MONGODB_DB_NAME = db_config['database'] or os.getenv("DATABASE_NAME") or os.getenv("MONGODB_DB_NAME")
    
    logger.debug(
        "Attempting to connect to MongoDB",
        metadata={"event": "mongodb_connect_attempt", "uri": f"{db_config['host']}:{db_config['port']}", "db_name": MONGODB_DB_NAME}
    )
    
    # Validate required environment variables
    if not db_config['host']:
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
