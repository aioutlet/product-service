"""
Product repository for domain-specific data access operations.

Extends BaseRepository with product-specific queries including:
- Text search with filters
- Category-based queries
- SKU and brand lookups
- Aggregation pipelines
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Any, Dict, List, Optional, Tuple
from pymongo.errors import PyMongoError

from src.repositories.base_repository import BaseRepository
from src.core.logger import logger


class ProductRepository(BaseRepository):
    """
    Repository for product-specific data access operations.
    
    Provides domain-specific methods for:
    - Product search with text and filters
    - Category aggregations
    - SKU uniqueness checks
    - Brand filtering
    """
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """Initialize product repository with products collection."""
        super().__init__(collection, dict)  # Using dict as we'll handle models in service layer
    
    async def search_products(
        self,
        search_text: str,
        department: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 10,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search products with text and filters.
        
        Uses MongoDB text search index for better performance and relevance scoring.
        
        Args:
            search_text: Text to search in name, description, tags, searchKeywords
            department: Department filter
            category: Category filter
            subcategory: Subcategory filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            tags: Tags filter (any match)
            skip: Number of documents to skip
            limit: Maximum documents to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (list of products, total count)
        """
        try:
            # Build query for active products only
            query = {"is_active": True}
            
            # MongoDB text search using text index (faster and supports relevance scoring)
            if search_text:
                query["$text"] = {"$search": search_text.strip()}
            
            # Hierarchical taxonomy filters
            if department:
                query["department"] = {"$regex": f"^{department}$", "$options": "i"}
            if category:
                query["category"] = {"$regex": f"^{category}$", "$options": "i"}
            if subcategory:
                query["subcategory"] = {"$regex": f"^{subcategory}$", "$options": "i"}
            
            # Price range filter
            if min_price is not None or max_price is not None:
                price_query = {}
                if min_price is not None:
                    price_query["$gte"] = min_price
                if max_price is not None:
                    price_query["$lte"] = max_price
                query["price"] = price_query
            
            # Tags filter
            if tags:
                query["tags"] = {"$in": tags}
            
            logger.debug(
                "Searching products",
                correlation_id=correlation_id,
                metadata={
                    "search_text": search_text,
                    "filters": {
                        "department": department,
                        "category": category,
                        "subcategory": subcategory,
                        "price_range": f"{min_price}-{max_price}",
                        "tags": tags
                    }
                }
            )
            
            # Execute query with pagination
            # When using $text search, we can sort by relevance score { "score": { "$meta": "textScore" } }
            # For now, keeping default sorting. To add relevance sorting:
            # sort = [("score", {"$meta": "textScore"})] if search_text else None
            products = await self.find_many(query, skip=skip, limit=limit, correlation_id=correlation_id)
            total_count = await self.count(query, correlation_id=correlation_id)
            
            return products, total_count
        
        except PyMongoError as e:
            logger.error(
                "MongoDB error during product search",
                correlation_id=correlation_id,
                error=e,
                metadata={"search_text": search_text}
            )
            raise
    
    async def get_top_categories(
        self,
        limit: int = 5,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top categories by product count.
        
        Args:
            limit: Maximum number of categories to return
            correlation_id: Correlation ID for logging
            
        Returns:
            List of categories with metadata
        """
        try:
            pipeline = [
                # Filter: only active products with valid categories
                {
                    "$match": {
                        "is_active": True,
                        "category": {"$exists": True, "$ne": None, "$ne": ""}
                    }
                },
                # Group by category and count
                {
                    "$group": {
                        "_id": "$category",
                        "count": {"$sum": 1},
                        "products": {"$push": "$$ROOT"}
                    }
                },
                # Sort by count descending
                {"$sort": {"count": -1}},
                # Limit results
                {"$limit": limit},
                # Project final shape
                {
                    "$project": {
                        "category": "$_id",
                        "product_count": "$count",
                        "_id": 0
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            categories = await cursor.to_list(length=limit)
            
            logger.debug(
                f"Retrieved {len(categories)} top categories",
                correlation_id=correlation_id,
                metadata={"count": len(categories)}
            )
            
            return categories
        
        except PyMongoError as e:
            logger.error(
                "Error getting top categories",
                correlation_id=correlation_id,
                error=e
            )
            raise
    
    async def find_by_sku(
        self,
        sku: str,
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find product by SKU.
        
        Args:
            sku: Product SKU
            correlation_id: Correlation ID for logging
            
        Returns:
            Product document if found
        """
        return await self.find_one({"sku": sku}, correlation_id=correlation_id)
    
    async def find_by_department(
        self,
        department: str,
        skip: int = 0,
        limit: int = 10,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find products by department.
        
        Args:
            department: Department name
            skip: Number to skip
            limit: Maximum to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (products, total count)
        """
        query = {"department": {"$regex": f"^{department}$", "$options": "i"}, "is_active": True}
        
        products = await self.find_many(query, skip=skip, limit=limit, correlation_id=correlation_id)
        total_count = await self.count(query, correlation_id=correlation_id)
        
        return products, total_count
    
    async def find_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 10,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find products by category.
        
        Args:
            category: Category name
            skip: Number to skip
            limit: Maximum to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (products, total count)
        """
        query = {"category": {"$regex": f"^{category}$", "$options": "i"}, "is_active": True}
        
        products = await self.find_many(query, skip=skip, limit=limit, correlation_id=correlation_id)
        total_count = await self.count(query, correlation_id=correlation_id)
        
        return products, total_count
    
    async def find_by_brand(
        self,
        brand: str,
        skip: int = 0,
        limit: int = 10,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find products by brand.
        
        Args:
            brand: Brand name
            skip: Number to skip
            limit: Maximum to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (products, total count)
        """
        query = {"brand": {"$regex": f"^{brand}$", "$options": "i"}, "is_active": True}
        
        products = await self.find_many(query, skip=skip, limit=limit, correlation_id=correlation_id)
        total_count = await self.count(query, correlation_id=correlation_id)
        
        return products, total_count
    
    async def is_sku_unique(
        self,
        sku: str,
        exclude_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Check if SKU is unique (for creation/update validation).
        
        Args:
            sku: SKU to check
            exclude_id: Product ID to exclude (for updates)
            correlation_id: Correlation ID for logging
            
        Returns:
            True if SKU is unique
        """
        query = {"sku": sku}
        
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        
        exists = await self.exists(query, correlation_id=correlation_id)
        return not exists
    
    async def get_active_products(
        self,
        skip: int = 0,
        limit: int = 10,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all active products with pagination.
        
        Args:
            skip: Number to skip
            limit: Maximum to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (products, total count)
        """
        query = {"is_active": True}
        
        products = await self.find_many(query, skip=skip, limit=limit, correlation_id=correlation_id)
        total_count = await self.count(query, correlation_id=correlation_id)
        
        return products, total_count
    
    async def soft_delete(
        self,
        product_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Soft delete a product (set is_active=False).
        
        Args:
            product_id: Product ID to soft delete
            correlation_id: Correlation ID for logging
            
        Returns:
            True if successful
        """
        return await self.update(
            product_id,
            {"$set": {"is_active": False}},
            correlation_id=correlation_id
        )
