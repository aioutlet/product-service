import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_CONNECTION_SCHEME", "mongodb") + "://"
if os.getenv("MONGODB_USERNAME") and os.getenv("MONGODB_PASSWORD"):
    MONGODB_URI += f"{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@"
MONGODB_URI += f"{os.getenv('MONGODB_HOST', 'localhost')}:{os.getenv('MONGODB_PORT', '27017')}"
if os.getenv("MONGODB_DB_PARAMS"):
    MONGODB_URI += f"/?{os.getenv('MONGODB_DB_PARAMS')}"
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

async def clean():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    products_col = db["products"]
    result = await products_col.delete_many({})
    print(f"Deleted {result.deleted_count} products.")
    client.close()

if __name__ == "__main__":
    asyncio.run(clean())
