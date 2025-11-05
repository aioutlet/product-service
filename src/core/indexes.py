"""
Database index management for MongoDB.

Creates and manages indexes for optimal query performance.
Indexes are created at application startup.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT
from src.core.logger import logger


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Create all required MongoDB indexes for the product collection.
    
    This function should be called during application startup to ensure
    all indexes exist before the service starts handling requests.
    
    Args:
        db: MongoDB database instance
    """
    collection = db["products"]
    
    try:
        # 1. SKU Unique Index (prevent duplicate SKUs)
        await collection.create_index(
            [("sku", ASCENDING)],
            unique=True,
            sparse=True,  # Allow null SKUs during creation
            name="idx_sku_unique"
        )
        logger.info("Created unique index on 'sku'")
        
        # 2. Status + Category + Price (common filter combination)
        await collection.create_index(
            [
                ("is_active", ASCENDING),
                ("taxonomy.category", ASCENDING),
                ("price", ASCENDING)
            ],
            name="idx_status_category_price"
        )
        logger.info("Created compound index on 'is_active', 'taxonomy.category', 'price'")
        
        # 3. Status + Department + Price
        await collection.create_index(
            [
                ("is_active", ASCENDING),
                ("taxonomy.department", ASCENDING),
                ("price", ASCENDING)
            ],
            name="idx_status_department_price"
        )
        logger.info("Created compound index on 'is_active', 'taxonomy.department', 'price'")
        
        # 4. Status + Rating (sorting by rating)
        await collection.create_index(
            [
                ("is_active", ASCENDING),
                ("reviewAggregates.averageRating", DESCENDING)
            ],
            name="idx_status_rating"
        )
        logger.info("Created compound index on 'is_active', 'reviewAggregates.averageRating'")
        
        # 5. Status + Created Date (recent products)
        await collection.create_index(
            [
                ("is_active", ASCENDING),
                ("createdAt", DESCENDING)
            ],
            name="idx_status_created"
        )
        logger.info("Created compound index on 'is_active', 'createdAt'")
        
        # 6. Brand Index (filter by brand)
        await collection.create_index(
            [("brand", ASCENDING)],
            name="idx_brand"
        )
        logger.info("Created index on 'brand'")
        
        # 7. Tags Index (filter by tags)
        await collection.create_index(
            [("tags", ASCENDING)],
            name="idx_tags"
        )
        logger.info("Created index on 'tags'")
        
        # 8. Parent ID Index (for variations)
        await collection.create_index(
            [("parentId", ASCENDING)],
            sparse=True,
            name="idx_parent_id"
        )
        logger.info("Created index on 'parentId'")
        
        # 9. Full-Text Search Index (name, description, tags, searchKeywords)
        await collection.create_index(
            [
                ("name", TEXT),
                ("description", TEXT),
                ("tags", TEXT),
                ("searchKeywords", TEXT)
            ],
            weights={
                "name": 10,           # Highest weight
                "tags": 5,            # Medium-high weight
                "searchKeywords": 5,  # Medium-high weight
                "description": 2      # Lower weight
            },
            name="idx_text_search"
        )
        logger.info("Created text search index on 'name', 'description', 'tags', 'searchKeywords'")
        
        # 10. Badges Index (filter by badges)
        await collection.create_index(
            [("badges", ASCENDING)],
            name="idx_badges"
        )
        logger.info("Created index on 'badges'")
        
        logger.info("✅ All database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database indexes: {str(e)}")
        raise


async def list_indexes(db: AsyncIOMotorDatabase) -> list:
    """
    List all indexes on the products collection.
    
    Useful for debugging and verification.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        List of index information dictionaries
    """
    collection = db["products"]
    indexes = await collection.list_indexes().to_list(None)
    return indexes
