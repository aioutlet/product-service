import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_CONNECTION_SCHEME", "mongodb") + "://"
if os.getenv("MONGODB_USERNAME") and os.getenv("MONGODB_PASSWORD"):
    MONGODB_URI += f"{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@"
MONGODB_URI += f"{os.getenv('MONGODB_HOST', 'localhost')}:{os.getenv('MONGODB_PORT', '27017')}"
if os.getenv("MONGODB_DB_PARAMS"):
    MONGODB_URI += f"/?{os.getenv('MONGODB_DB_PARAMS')}"
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

def load_products_from_json():
    """Load products from the products-data.json file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "products-data.json")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            products_data = json.load(file)
        
        # Add required fields for each product
        for product in products_data:
            # Add missing fields that are required by the model
            product.setdefault("variants", [])
            product.setdefault("average_rating", 0)
            product.setdefault("num_reviews", 0)
            product.setdefault("reviews", [])
            product.setdefault("created_by", "6859c9bd49fa695169361c82")  # Admin user ObjectId from user-service
            product.setdefault("updated_by", None)
            product["created_at"] = datetime.utcnow()
            product["updated_at"] = datetime.utcnow()
            product.setdefault("is_active", True)
            product.setdefault("history", [])
        
        return products_data
    
    except FileNotFoundError:
        print(f"Error: products-data.json not found at {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing products-data.json: {e}")
        return []

async def seed():
    """Seed the database with products from products-data.json"""
    products = load_products_from_json()
    
    if not products:
        print("No products to seed. Please check products-data.json file.")
        return
    
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    products_col = db["products"]
    
    try:
        # Clear existing products first (optional)
        existing_count = await products_col.count_documents({})
        if existing_count > 0:
            print(f"Found {existing_count} existing products. Clearing collection...")
            await products_col.delete_many({})
        
        # Insert new products
        result = await products_col.insert_many(products)
        print(f"Successfully seeded {len(result.inserted_ids)} products.")
        
        # Print some stats
        print(f"\nProducts by category:")
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        async for doc in products_col.aggregate(pipeline):
            print(f"  {doc['_id']}: {doc['count']} products")
            
    except Exception as e:
        print(f"Error seeding products: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed())
