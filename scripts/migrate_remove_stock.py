#!/usr/bin/env python3
"""
Migration Script: Remove Stock Fields from Product Service

This script removes in_stock fields from all products in the MongoDB database
to implement proper microservices separation between product and inventory services.

Usage:
    python scripts/migrate_remove_stock.py
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add the src directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.logger import get_logger

logger = get_logger(__name__)

async def migrate_remove_stock_fields():
    """
    Remove in_stock fields from all products in the database.
    """
    # MongoDB connection string (adjust as needed)
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "aioutlet_products")
    
    client = None
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client[database_name]
        collection = db["products"]
        
        logger.info("Connected to MongoDB, starting migration...")
        
        # Count total products
        total_products = await collection.count_documents({})
        logger.info(f"Found {total_products} total products")
        
        # Count products with in_stock field
        products_with_stock = await collection.count_documents({"in_stock": {"$exists": True}})
        logger.info(f"Found {products_with_stock} products with in_stock field")
        
        if products_with_stock == 0:
            logger.info("No products have in_stock field. Migration not needed.")
            return
        
        # Update all products to remove in_stock field
        result = await collection.update_many(
            {"in_stock": {"$exists": True}},
            {
                "$unset": {"in_stock": ""},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "updated_by": "migration_script"
                }
            }
        )
        
        logger.info(f"Migration completed successfully!")
        logger.info(f"Modified {result.modified_count} products")
        logger.info(f"Matched {result.matched_count} products")
        
        # Verify migration
        remaining_with_stock = await collection.count_documents({"in_stock": {"$exists": True}})
        if remaining_with_stock == 0:
            logger.info("✅ Migration verification passed - no products have in_stock field")
        else:
            logger.error(f"❌ Migration verification failed - {remaining_with_stock} products still have in_stock field")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    print("🔄 Starting migration: Remove stock fields from product service")
    print("=" * 60)
    
    try:
        asyncio.run(migrate_remove_stock_fields())
        print("\n✅ Migration completed successfully!")
        print("📋 Summary:")
        print("   - Removed in_stock fields from all products")
        print("   - Stock management is now handled by inventory-service")
        print("   - Use ProductWithInventory endpoints for combined data")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
