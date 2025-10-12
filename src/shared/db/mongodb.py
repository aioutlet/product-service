import os

from motor.motor_asyncio import AsyncIOMotorClient

from src.shared.core.errors import ErrorResponse
from src.shared.core.logger import logger


async def get_db():
    MONGODB_CONNECTION_SCHEME = os.getenv("MONGODB_CONNECTION_SCHEME", "mongodb")
    MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT = os.getenv("MONGODB_PORT", "27017")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
    MONGODB_DB_PARAMS = os.getenv("MONGODB_DB_PARAMS", "")

    if not MONGODB_DB_NAME:
        logger.error(
            "MONGODB_DB_NAME must be set in the environment or .env file",
            extra={"event": "mongodb_env_error"},
        )
        raise RuntimeError(
            "MONGODB_DB_NAME must be set in the environment or .env file"
        )

    if MONGODB_USERNAME and MONGODB_PASSWORD:
        auth = f"{MONGODB_USERNAME}:{MONGODB_PASSWORD}@"
    else:
        auth = ""
    params = f"?{MONGODB_DB_PARAMS}" if MONGODB_DB_PARAMS else ""
    MONGODB_URI = (
        f"{MONGODB_CONNECTION_SCHEME}://{auth}{MONGODB_HOST}:{MONGODB_PORT}/{params}"
    )
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]

    # Test if the database exists by listing its collections
    try:
        collections = await db.list_collection_names()
        if not collections:
            logger.error(
                f"MongoDB database '{MONGODB_DB_NAME}' has no collections "
                "and is not set up.",
                extra={"event": "mongodb_db_empty"},
            )
            raise ErrorResponse(
                f"MongoDB database '{MONGODB_DB_NAME}' has no collections "
                "and is not set up.",
                status_code=503,
            )
    except Exception as e:
        logger.error(
            f"MongoDB database '{MONGODB_DB_NAME}' is not accessible: {e}",
            extra={"event": "mongodb_db_missing"},
        )
        raise ErrorResponse(
            f"MongoDB database '{MONGODB_DB_NAME}' is not accessible: {e}",
            status_code=503,
        )

    return db


async def get_product_collection():
    db = await get_db()
    collections = await db.list_collection_names()
    if "products" not in collections:
        logger.error(
            f"'products' collection does not exist in database '{db.name}'.",
            extra={"event": "mongodb_collection_missing"},
        )
        raise ErrorResponse(
            f"'products' collection does not exist in database '{db.name}'. "
            "Please create it before using the service.",
            status_code=404,
        )
    return db["products"]
