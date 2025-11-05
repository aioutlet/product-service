"""
Attribute Schema Repository

MongoDB storage for product attribute schemas.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from src.models.attribute_schema import CategorySchema
from src.models.standard_schemas import StandardSchemas
from src.core.logger import logger


class AttributeSchemaRepository:
    """
    Repository for managing attribute schemas in MongoDB.
    
    Provides CRUD operations for category schemas.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with database connection"""
        self.db = db
        self.collection = db.attribute_schemas
    
    async def create(
        self,
        schema: CategorySchema,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Create a new attribute schema.
        
        Args:
            schema: Category schema to create
            correlation_id: For logging
            
        Returns:
            Created schema ID
        """
        logger.info(
            f"Creating schema for category: {schema.category_name}",
            correlation_id=correlation_id
        )
        
        # Convert to dict for MongoDB
        schema_dict = schema.model_dump()
        schema_dict["created_at"] = datetime.now(UTC)
        schema_dict["updated_at"] = datetime.now(UTC)
        
        # Insert
        result = await self.collection.insert_one(schema_dict)
        
        logger.info(
            f"Created schema {result.inserted_id} for category {schema.category_name}",
            correlation_id=correlation_id
        )
        
        return str(result.inserted_id)
    
    async def update(
        self,
        category: str,
        schema: CategorySchema,
        correlation_id: Optional[str] = None
    ):
        """
        Update an existing attribute schema.
        
        Args:
            category: Category name
            schema: Updated schema
            correlation_id: For logging
        """
        logger.info(
            f"Updating schema for category: {category}",
            correlation_id=correlation_id
        )
        
        # Convert to dict
        schema_dict = schema.model_dump()
        schema_dict["updated_at"] = datetime.now(UTC)
        
        # Update
        result = await self.collection.update_one(
            {"category_name": category},
            {"$set": schema_dict}
        )
        
        logger.info(
            f"Updated schema for category {category} (matched={result.matched_count})",
            correlation_id=correlation_id
        )
    
    async def get_by_category(
        self,
        category: str,
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get schema by category name.
        
        Args:
            category: Category name
            correlation_id: For logging
            
        Returns:
            Schema dict or None if not found
        """
        logger.debug(f"Getting schema for category: {category}", correlation_id=correlation_id)
        
        schema = await self.collection.find_one({"category_name": category})
        
        if not schema:
            logger.warning(f"Schema not found for category: {category}", correlation_id=correlation_id)
        
        return schema
    
    async def list_all(
        self,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all attribute schemas.
        
        Args:
            correlation_id: For logging
            
        Returns:
            List of schema dicts
        """
        logger.debug("Listing all schemas", correlation_id=correlation_id)
        
        cursor = self.collection.find({})
        schemas = await cursor.to_list(length=100)
        
        logger.info(f"Found {len(schemas)} schemas", correlation_id=correlation_id)
        
        return schemas
    
    async def delete(
        self,
        category: str,
        correlation_id: Optional[str] = None
    ):
        """
        Delete an attribute schema.
        
        Args:
            category: Category name
            correlation_id: For logging
        """
        logger.info(f"Deleting schema for category: {category}", correlation_id=correlation_id)
        
        result = await self.collection.delete_one({"category_name": category})
        
        logger.info(
            f"Deleted schema for category {category} (deleted={result.deleted_count})",
            correlation_id=correlation_id
        )
    
    async def seed_standard_schemas(
        self,
        correlation_id: Optional[str] = None
    ):
        """
        Seed database with standard category schemas.
        
        Args:
            correlation_id: For logging
        """
        logger.info("Seeding standard schemas", correlation_id=correlation_id)
        
        standard_schemas = StandardSchemas.get_all_schemas()
        
        for schema in standard_schemas:
            # Check if already exists
            existing = await self.get_by_category(schema.category_name, correlation_id)
            
            if not existing:
                await self.create(schema, correlation_id)
                logger.info(f"Seeded schema for {schema.category_name}", correlation_id=correlation_id)
            else:
                logger.debug(f"Schema already exists for {schema.category_name}", correlation_id=correlation_id)
        
        logger.info(f"Seeded {len(standard_schemas)} standard schemas", correlation_id=correlation_id)
