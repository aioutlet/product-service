#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ProductDatabaseSeeder:
    def __init__(self):
        # Get MongoDB connection string from environment
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("DATABASE_NAME") or os.getenv("MONGODB_DB_NAME")
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI must be set in environment or .env file")
        
        if not self.db_name:
            raise ValueError("DATABASE_NAME or MONGODB_DB_NAME must be set in environment or .env file")
        
        self.client = None
        self.db = None
        
    async def connect(self):
        """Establish MongoDB connection"""
        print(f"Connecting to MongoDB database '{self.db_name}'...")
        self.client = AsyncIOMotorClient(self.mongodb_uri)
        self.db = self.client[self.db_name]
        
        # Test connection
        await self.db.command('ping')
        print("Successfully connected to MongoDB!")

    async def seed_data(self):
        """Main seeding method"""
        print("Seeding product service data...")

        try:
            # Clear existing data
            await self.clear_data()

            # Seed products
            await self.seed_products()

            print("Product service data seeding completed successfully!")
        except Exception as error:
            print(f"Error seeding product data: {error}")
            raise error

    async def clear_data(self):
        """Clear existing product data"""
        print("Clearing existing product data...")
        
        collections = await self.db.list_collection_names()
        
        if "products" in collections:
            result = await self.db.products.delete_many({})
            print(f"Deleted {result.deleted_count} existing products")
        else:
            print("No existing products collection found")

    async def seed_products(self):
        """Seed products from JSON file"""
        # Try products-data.json first (primary source)
        products_data_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "products.json"
        )
       
        products_data = []
        source_file = None
        
        if os.path.exists(products_data_path):
            source_file = products_data_path
            print(f"Loading products from: {products_data_path}")
            with open(products_data_path, "r") as f:
                products_data = json.load(f)
        elif os.path.exists(products_seeds_path):
            source_file = products_seeds_path
            print(f"Loading products from: {products_seeds_path}")
            with open(products_seeds_path, "r") as f:
                products_data = json.load(f)
        else:
            print(f"No products data file found. Checked:")
            print(f"  - {products_data_path}")
            print(f"  - {products_seeds_path}")
            print("Creating sample products...")
            await self.create_sample_products()
            return

        # Transform products to match MongoDB schema
        products = []
        for idx, product in enumerate(products_data, 1):
            # Calculate rating and reviews from in_stock quantity as a proxy
            # Higher stock = more popular = more reviews
            stock_quantity = product.get("in_stock", 50)
            base_rating = 4.0 + (min(stock_quantity, 150) / 150) * 0.9  # 4.0 to 4.9
            num_reviews = max(3, int(stock_quantity * 0.8))  # At least 3 reviews
            
            # Map JSON data to MongoDB schema
            product_doc = {
                "name": product.get("name"),
                "description": product.get("description"),
                "price": float(product.get("price", 0)),
                "category": product.get("category"),
                "brand": product.get("brand"),
                "sku": product.get("sku"),
                "images": product.get("images", []),
                "tags": product.get("tags", []),
                "attributes": product.get("attributes", {}),
                "variants": [],
                "average_rating": round(base_rating, 1),
                "num_reviews": num_reviews,
                "reviews": [],
                "created_by": "system",
                "updated_by": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
            products.append(product_doc)

        if products:
            result = await self.db.products.insert_many(products)
            print(f"Successfully seeded {len(result.inserted_ids)} products from {source_file}")
        else:
            print("No products to seed")

    async def create_sample_products(self):
        """Create sample products for testing"""
        sample_products = [
            {
                "name": "Wireless Bluetooth Headphones",
                "description": "Premium noise-canceling wireless headphones with 30-hour battery life",
                "price": 149.99,
                "category": "Electronics",
                "brand": "TechSound",
                "sku": "TS-WH-001",
                "images": [
                    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
                    "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800"
                ],
                "tags": ["wireless", "bluetooth", "headphones", "noise-canceling"],
                "attributes": {"color": "Black", "connectivity": "Bluetooth 5.0", "battery": "30 hours"},
                "variants": [],
                "average_rating": 4.7,
                "num_reviews": 156,
                "reviews": [],
                "created_by": "system",
                "updated_by": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "name": "Smart Fitness Watch",
                "description": "Track your health and fitness goals with this advanced smartwatch featuring heart rate monitoring and GPS",
                "price": 299.99,
                "category": "Wearables",
                "brand": "FitTech",
                "sku": "FT-SW-002",
                "images": [
                    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800",
                    "https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=800"
                ],
                "tags": ["smartwatch", "fitness", "health", "gps"],
                "attributes": {"color": "Silver", "display": "AMOLED", "waterproof": "5ATM"},
                "variants": [],
                "average_rating": 4.5,
                "num_reviews": 203,
                "reviews": [],
                "created_by": "system",
                "updated_by": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "name": "Portable Bluetooth Speaker",
                "description": "Waterproof portable speaker with 360-degree sound and 12-hour playtime",
                "price": 79.99,
                "category": "Electronics",
                "brand": "SoundWave",
                "sku": "SW-BS-003",
                "images": [
                    "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800"
                ],
                "tags": ["speaker", "bluetooth", "portable", "waterproof"],
                "attributes": {"color": "Blue", "battery": "12 hours", "waterproof": "IPX7"},
                "variants": [],
                "average_rating": 4.3,
                "num_reviews": 89,
                "reviews": [],
                "created_by": "system",
                "updated_by": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "name": "Mechanical Gaming Keyboard",
                "description": "RGB backlit mechanical keyboard with customizable keys and macro support",
                "price": 129.99,
                "category": "Gaming",
                "brand": "GameTech",
                "sku": "GT-KB-004",
                "images": [
                    "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800"
                ],
                "tags": ["keyboard", "gaming", "mechanical", "rgb"],
                "attributes": {"switches": "Cherry MX Blue", "backlight": "RGB", "connectivity": "USB-C"},
                "variants": [],
                "average_rating": 4.8,
                "num_reviews": 342,
                "reviews": [],
                "created_by": "system",
                "updated_by": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "name": "4K Webcam",
                "description": "Professional 4K webcam with auto-focus and built-in noise-canceling microphone",
                "price": 199.99,
                "category": "Electronics",
                "brand": "StreamPro",
                "sku": "SP-WC-005",
                "images": [
                    "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=800"
                ],
                "tags": ["webcam", "4k", "streaming", "video"],
                "attributes": {"resolution": "4K", "framerate": "30fps", "mic": "Built-in"},
                "variants": [],
                "average_rating": 4.6,
                "num_reviews": 127,
                "reviews": [],
                "created_by": "system",
                "updated_by": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
        ]
        
        result = await self.db.products.insert_many(sample_products)
        print(f"Created {len(result.inserted_ids)} sample products")

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")


async def main():
    load_dotenv()
    seeder = ProductDatabaseSeeder()

    try:
        print("=" * 50)
        print("Product Service Database Seeder")
        print("=" * 50)

        await seeder.connect()
        await seeder.seed_data()

        print("=" * 50)
        print("Product database setup completed!")
        print("=" * 50)
    except Exception as error:
        print(f"Product database setup failed: {error}")
        exit(1)
    finally:
        await seeder.close()


if __name__ == "__main__":
    asyncio.run(main())
