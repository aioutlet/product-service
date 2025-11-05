"""
Size Chart Repository

Data access layer for size chart operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection

from src.core.logger import logger


class SizeChartRepository:
    """Repository for size chart data access operations"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Initialize repository with MongoDB collection.
        
        Args:
            collection: MongoDB collection for size charts
        """
        self.collection = collection
    
    async def create(
        self,
        size_chart_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Create a new size chart.
        
        Args:
            size_chart_data: Size chart document data
            correlation_id: Request correlation ID
            
        Returns:
            Created size chart ID
        """
        try:
            # Add timestamps
            now = datetime.now(timezone.utc)
            size_chart_data["created_at"] = now
            size_chart_data["updated_at"] = now
            size_chart_data["is_active"] = size_chart_data.get("is_active", True)
            size_chart_data["usage_count"] = 0
            
            result = await self.collection.insert_one(size_chart_data)
            
            logger.info(
                "Size chart created",
                metadata={
                    "size_chart_id": str(result.inserted_id),
                    "category": size_chart_data.get("category"),
                    "correlation_id": correlation_id
                }
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(
                "Error creating size chart",
                error=e,
                metadata={"correlation_id": correlation_id}
            )
            raise
    
    async def find_by_id(
        self,
        size_chart_id: str,
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find size chart by ID.
        
        Args:
            size_chart_id: Size chart ID
            correlation_id: Request correlation ID
            
        Returns:
            Size chart document or None
        """
        try:
            from bson import ObjectId
            chart = await self.collection.find_one({"_id": ObjectId(size_chart_id)})
            
            if chart:
                chart["_id"] = str(chart["_id"])
            
            return chart
            
        except Exception as e:
            logger.error(
                "Error finding size chart",
                error=e,
                metadata={
                    "size_chart_id": size_chart_id,
                    "correlation_id": correlation_id
                }
            )
            return None
    
    async def find_by_category(
        self,
        category: str,
        include_inactive: bool = False,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find size charts by category.
        
        Args:
            category: Product category
            include_inactive: Whether to include inactive charts
            correlation_id: Request correlation ID
            
        Returns:
            List of size charts
        """
        try:
            query = {"category": category}
            if not include_inactive:
                query["is_active"] = True
            
            cursor = self.collection.find(query).sort("created_at", -1)
            charts = await cursor.to_list(length=100)
            
            # Convert ObjectId to string
            for chart in charts:
                chart["_id"] = str(chart["_id"])
            
            return charts
            
        except Exception as e:
            logger.error(
                "Error finding size charts by category",
                error=e,
                metadata={"category": category, "correlation_id": correlation_id}
            )
            return []
    
    async def find_templates(
        self,
        category: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find size chart templates.
        
        Args:
            category: Optional category filter
            correlation_id: Request correlation ID
            
        Returns:
            List of template size charts
        """
        try:
            query = {"is_template": True, "is_active": True}
            if category:
                query["category"] = category
            
            cursor = self.collection.find(query).sort("name", 1)
            templates = await cursor.to_list(length=100)
            
            for template in templates:
                template["_id"] = str(template["_id"])
            
            return templates
            
        except Exception as e:
            logger.error(
                "Error finding size chart templates",
                error=e,
                metadata={"correlation_id": correlation_id}
            )
            return []
    
    async def update(
        self,
        size_chart_id: str,
        update_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update size chart.
        
        Args:
            size_chart_id: Size chart ID
            update_data: Fields to update
            correlation_id: Request correlation ID
            
        Returns:
            Updated size chart or None
        """
        try:
            from bson import ObjectId
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(size_chart_id)},
                {"$set": update_data},
                return_document=True
            )
            
            if result:
                result["_id"] = str(result["_id"])
                logger.info(
                    "Size chart updated",
                    metadata={
                        "size_chart_id": size_chart_id,
                        "correlation_id": correlation_id
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error updating size chart",
                error=e,
                metadata={
                    "size_chart_id": size_chart_id,
                    "correlation_id": correlation_id
                }
            )
            return None
    
    async def delete(
        self,
        size_chart_id: str,
        soft_delete: bool = True,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Delete size chart (soft delete by default).
        
        Args:
            size_chart_id: Size chart ID
            soft_delete: Whether to soft delete (set is_active=False)
            correlation_id: Request correlation ID
            
        Returns:
            True if deleted successfully
        """
        try:
            from bson import ObjectId
            
            if soft_delete:
                result = await self.collection.update_one(
                    {"_id": ObjectId(size_chart_id)},
                    {
                        "$set": {
                            "is_active": False,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                success = result.modified_count > 0
            else:
                result = await self.collection.delete_one(
                    {"_id": ObjectId(size_chart_id)}
                )
                success = result.deleted_count > 0
            
            if success:
                logger.info(
                    "Size chart deleted",
                    metadata={
                        "size_chart_id": size_chart_id,
                        "soft_delete": soft_delete,
                        "correlation_id": correlation_id
                    }
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Error deleting size chart",
                error=e,
                metadata={
                    "size_chart_id": size_chart_id,
                    "correlation_id": correlation_id
                }
            )
            return False
    
    async def increment_usage_count(
        self,
        size_chart_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Increment usage count when size chart is assigned to a product.
        
        Args:
            size_chart_id: Size chart ID
            correlation_id: Request correlation ID
            
        Returns:
            True if incremented successfully
        """
        try:
            from bson import ObjectId
            
            result = await self.collection.update_one(
                {"_id": ObjectId(size_chart_id)},
                {"$inc": {"usage_count": 1}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(
                "Error incrementing usage count",
                error=e,
                metadata={
                    "size_chart_id": size_chart_id,
                    "correlation_id": correlation_id
                }
            )
            return False
    
    async def decrement_usage_count(
        self,
        size_chart_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Decrement usage count when size chart is unassigned from a product.
        
        Args:
            size_chart_id: Size chart ID
            correlation_id: Request correlation ID
            
        Returns:
            True if decremented successfully
        """
        try:
            from bson import ObjectId
            
            result = await self.collection.update_one(
                {"_id": ObjectId(size_chart_id)},
                {"$inc": {"usage_count": -1}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(
                "Error decrementing usage count",
                error=e,
                metadata={
                    "size_chart_id": size_chart_id,
                    "correlation_id": correlation_id
                }
            )
            return False
    
    async def list_all(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all size charts with pagination.
        
        Args:
            include_inactive: Include inactive charts
            skip: Number of records to skip
            limit: Maximum records to return
            correlation_id: Request correlation ID
            
        Returns:
            List of size charts
        """
        try:
            query = {}
            if not include_inactive:
                query["is_active"] = True
            
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            charts = await cursor.to_list(length=limit)
            
            for chart in charts:
                chart["_id"] = str(chart["_id"])
            
            return charts
            
        except Exception as e:
            logger.error(
                "Error listing size charts",
                error=e,
                metadata={"correlation_id": correlation_id}
            )
            return []
