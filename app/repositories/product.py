"""
Product repository for data access layer following Repository pattern
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId

from pymongo.errors import PyMongoError
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.errors import ErrorResponse
from app.core.logger import logger
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse


class ProductRepository:
    """Repository for product data access operations"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    def _doc_to_response(self, doc: dict) -> ProductResponse:
        """Convert MongoDB document to ProductResponse schema"""
        if not doc:
            return None
            
        # Convert ObjectId to string
        doc["id"] = str(doc.pop("_id"))
        
        # Handle datetime fields
        for field in ["created_at", "updated_at"]:
            if field in doc and not isinstance(doc[field], datetime):
                doc[field] = datetime.now(timezone.utc)
        
        # Handle history datetime conversion
        if "history" in doc:
            for entry in doc.get("history", []):
                if "updated_at" in entry and not isinstance(entry["updated_at"], datetime):
                    entry["updated_at"] = datetime.now(timezone.utc)
        
        # Ensure review_aggregates is not None - create default if missing
        if doc.get("review_aggregates") is None:
            from app.models.product import ReviewAggregates
            doc["review_aggregates"] = ReviewAggregates().model_dump()
        
        return ProductResponse(**doc)
    
    async def create(self, product_data: ProductCreate, created_by: str = "system") -> ProductResponse:
        """Create a new product"""
        try:
            # Prepare document for insertion
            doc = product_data.model_dump()
            doc.update({
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": created_by,
                "is_active": True,
                "history": []
            })
            
            # Insert document
            result = await self.collection.insert_one(doc)
            
            # Retrieve and return created product
            created_doc = await self.collection.find_one({"_id": result.inserted_id})
            return self._doc_to_response(created_doc)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error creating product: {e}")
            raise ErrorResponse("Database error during product creation", status_code=503)
    
    async def get_by_id(self, product_id: str) -> Optional[ProductResponse]:
        """Get product by ID"""
        try:
            # Validate ObjectId format
            if not ObjectId.is_valid(product_id):
                return None
                
            doc = await self.collection.find_one({"_id": ObjectId(product_id)})
            return self._doc_to_response(doc) if doc else None
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting product: {e}")
            raise ErrorResponse("Database error during product retrieval", status_code=503)
    
    async def update(self, product_id: str, product_data: ProductUpdate, updated_by: str = None) -> Optional[ProductResponse]:
        """Update an existing product"""
        try:
            # Validate ObjectId format
            if not ObjectId.is_valid(product_id):
                return None
            
            obj_id = ObjectId(product_id)
            
            # Get current product for change tracking
            current_doc = await self.collection.find_one({"_id": obj_id})
            if not current_doc:
                return None
            
            # Extract only fields that were set
            update_data = {k: v for k, v in product_data.model_dump(exclude_unset=True).items()}
            if not update_data:
                return self._doc_to_response(current_doc)
            
            # Track changes
            changes = {k: v for k, v in update_data.items() if k in current_doc and current_doc[k] != v}
            if changes and updated_by:
                history_entry = {
                    "updated_by": updated_by,
                    "updated_at": datetime.now(timezone.utc),
                    "changes": changes,
                }
                update_data.setdefault("history", current_doc.get("history", [])).append(history_entry)
            
            # Add update timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Perform update
            result = await self.collection.update_one(
                {"_id": obj_id}, 
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            # Return updated document
            updated_doc = await self.collection.find_one({"_id": obj_id})
            return self._doc_to_response(updated_doc)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error updating product: {e}")
            raise ErrorResponse("Database error during product update", status_code=503)
    
    async def delete(self, product_id: str) -> bool:
        """Soft delete a product"""
        try:
            # Validate ObjectId format
            if not ObjectId.is_valid(product_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
            )
            
            return result.matched_count > 0
            
        except PyMongoError as e:
            logger.error(f"MongoDB error deleting product: {e}")
            raise ErrorResponse("Database error during product deletion", status_code=503)
    
    async def reactivate(self, product_id: str, updated_by: str = None) -> Optional[ProductResponse]:
        """Reactivate a soft-deleted product"""
        try:
            # Validate ObjectId format
            if not ObjectId.is_valid(product_id):
                return None
            
            obj_id = ObjectId(product_id)
            
            # Get current product
            current_doc = await self.collection.find_one({"_id": obj_id})
            if not current_doc:
                return None
            
            # Check if already active
            if current_doc.get("is_active", True):
                return self._doc_to_response(current_doc)
            
            # Prepare update data
            update_data = {
                "is_active": True,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Add history entry if user provided
            if updated_by:
                history_entry = {
                    "updated_by": updated_by,
                    "updated_at": datetime.now(timezone.utc),
                    "changes": {"is_active": True, "action": "reactivated"},
                }
                await self.collection.update_one(
                    {"_id": obj_id},
                    {
                        "$set": update_data,
                        "$push": {"history": history_entry}
                    }
                )
            else:
                await self.collection.update_one(
                    {"_id": obj_id},
                    {"$set": update_data}
                )
            
            # Return updated document
            updated_doc = await self.collection.find_one({"_id": obj_id})
            return self._doc_to_response(updated_doc)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error reactivating product: {e}")
            raise ErrorResponse("Database error during product reactivation", status_code=503)
    
    async def search(self, 
                     search_text: str,
                     department: str = None,
                     category: str = None,
                     subcategory: str = None,
                     min_price: float = None,
                     max_price: float = None,
                     tags: List[str] = None,
                     skip: int = 0,
                     limit: int = None) -> tuple[List[ProductResponse], int]:
        """Search products with filters and pagination"""
        try:
            # Build query
            query = {"is_active": True}
            
            # Text search
            if search_text and search_text.strip():
                search_pattern = {"$regex": search_text.strip(), "$options": "i"}
                query["$or"] = [
                    {"name": search_pattern},
                    {"description": search_pattern},
                    {"tags": search_pattern},
                    {"brand": search_pattern},
                ]
            
            # Hierarchical filters - case insensitive regex (nested taxonomy)
            if department:
                query["taxonomy.department"] = {"$regex": f"^{department}$", "$options": "i"}
            if category:
                query["taxonomy.category"] = {"$regex": f"^{category}$", "$options": "i"}
            if subcategory:
                query["taxonomy.subcategory"] = {"$regex": f"^{subcategory}$", "$options": "i"}
            
            # Price range
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
            
            # Get total count
            total_count = await self.collection.count_documents(query)
            
            # Execute search with pagination
            cursor = self.collection.find(query).skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
                docs = await cursor.to_list(length=limit)
            else:
                docs = await cursor.to_list(length=None)
            
            # Convert to response models
            products = [self._doc_to_response(doc) for doc in docs]
            
            return products, total_count
            
        except PyMongoError as e:
            logger.error(f"MongoDB error during search: {e}")
            raise ErrorResponse("Database error during product search", status_code=503)
    
    async def list_products(self,
                           department: str = None,
                           category: str = None,
                           subcategory: str = None,
                           min_price: float = None,
                           max_price: float = None,
                           tags: List[str] = None,
                           skip: int = 0,
                           limit: int = None) -> tuple[List[ProductResponse], int]:
        """List products with filters and pagination"""
        try:
            query = {"is_active": True}
            
            # Log the collection name for debugging
            logger.info(
                f"Querying collection: {self.collection.name} in database: {self.collection.database.name}",
                metadata={"event": "query_debug", "collection": self.collection.name, "database": self.collection.database.name}
            )
            
            # Hierarchical filtering - case insensitive regex (nested taxonomy per PRD)
            if department:
                query["taxonomy.department"] = {"$regex": f"^{department}$", "$options": "i"}
            if category:
                query["taxonomy.category"] = {"$regex": f"^{category}$", "$options": "i"}
            if subcategory:
                query["taxonomy.subcategory"] = {"$regex": f"^{subcategory}$", "$options": "i"}
            
            # Price range filtering
            if min_price is not None or max_price is not None:
                price_query = {}
                if min_price is not None:
                    price_query["$gte"] = min_price
                if max_price is not None:
                    price_query["$lte"] = max_price
                query["price"] = price_query
            
            # Tags filtering
            if tags:
                query["tags"] = {"$in": tags}
            
            # Get total count
            total_count = await self.collection.count_documents(query)
            
            # Execute query with pagination
            cursor = self.collection.find(query).skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
                docs = await cursor.to_list(length=limit)
            else:
                docs = await cursor.to_list(length=None)
            
            # Convert to response models
            products = [self._doc_to_response(doc) for doc in docs]
            
            return products, total_count
            
        except PyMongoError as e:
            logger.error(f"MongoDB error listing products: {e}")
            raise ErrorResponse("Database error during product listing", status_code=503)
    
    async def get_trending_categories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get trending categories by product count (used by storefront-data endpoint only).
        This is an internal method for the combined storefront endpoint.
        """
        try:
            pipeline = [
                # Filter: only active products with valid categories
                {
                    "$match": {
                        "is_active": True,
                        "taxonomy.category": {"$exists": True, "$ne": None, "$ne": ""}
                    }
                },
                # Group by category and count
                {
                    "$group": {
                        "_id": "$taxonomy.category",
                        "product_count": {"$sum": 1},
                        "featured_product": {
                            "$first": {
                                "name": "$name",
                                "price": "$price",
                                "images": "$images"
                            }
                        }
                    }
                },
                # Sort by product count
                {"$sort": {"product_count": -1}},
                # Limit results
                {"$limit": limit},
                # Format output
                {
                    "$project": {
                        "_id": 0,
                        "name": "$_id",
                        "product_count": 1,
                        "featured_product": 1
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            categories = await cursor.to_list(length=limit)
            
            return categories
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting trending categories: {e}")
            raise ErrorResponse("Database error during trending categories retrieval", status_code=503)
    
    async def get_trending_products_with_scores(self, limit: int = 4) -> List[Dict]:
        """
        Get trending products with pre-calculated trending scores.
        
        Algorithm:
        - Base score = average_rating × total_review_count
        - Recency boost = 1.5x for products created in last 30 days
        - Minimum 3 reviews required (with fallbacks)
        """
        try:
            from datetime import datetime, timedelta, timezone
            
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Fetch candidate products (3x limit for filtering)
            candidate_limit = limit * 3
            
            pipeline = [
                {"$match": {"is_active": True}},
                # Add trending score calculation
                {"$addFields": {
                    "base_score": {
                        "$multiply": [
                            {"$ifNull": ["$review_aggregates.average_rating", 0]},
                            {"$ifNull": ["$review_aggregates.total_review_count", 0]}
                        ]
                    },
                    "is_recent": {
                        "$gte": ["$created_at", thirty_days_ago]
                    }
                }},
                {"$addFields": {
                    "trending_score": {
                        "$cond": {
                            "if": "$is_recent",
                            "then": {"$multiply": ["$base_score", 1.5]},
                            "else": "$base_score"
                        }
                    }
                }},
                # Priority filter: Products with 3+ reviews
                {"$match": {"review_aggregates.total_review_count": {"$gte": 3}}},
                {"$sort": {"trending_score": -1}},
                {"$limit": limit}
            ]
            
            docs = await self.collection.aggregate(pipeline).to_list(length=limit)
            
            # If not enough results, fallback to products with any reviews
            if len(docs) < limit:
                fallback_pipeline = [
                    {"$match": {"is_active": True}},
                    {"$addFields": {
                        "base_score": {
                            "$multiply": [
                                {"$ifNull": ["$review_aggregates.average_rating", 0]},
                                {"$ifNull": ["$review_aggregates.total_review_count", 0]}
                            ]
                        },
                        "is_recent": {"$gte": ["$created_at", thirty_days_ago]}
                    }},
                    {"$addFields": {
                        "trending_score": {
                            "$cond": {
                                "if": "$is_recent",
                                "then": {"$multiply": ["$base_score", 1.5]},
                                "else": "$base_score"
                            }
                        }
                    }},
                    {"$match": {"review_aggregates.total_review_count": {"$gt": 0}}},
                    {"$sort": {"trending_score": -1}},
                    {"$limit": candidate_limit}
                ]
                docs = await self.collection.aggregate(fallback_pipeline).to_list(length=candidate_limit)
            
            # Final fallback: Use recently created products
            if len(docs) < limit:
                cursor = self.collection.find({"is_active": True}).sort("created_at", -1).limit(limit)
                basic_docs = await cursor.to_list(length=limit)
                # Add default scores
                for doc in basic_docs:
                    doc["trending_score"] = 0
                    # Safely check if recent - handle both timezone-aware and naive datetimes
                    created_at = doc.get("created_at")
                    if created_at:
                        # Ensure timezone awareness for comparison
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        doc["is_recent"] = created_at >= thirty_days_ago
                    else:
                        doc["is_recent"] = False
                docs = basic_docs
            
            # Convert to response format with trending data
            products = []
            for doc in docs[:limit]:
                # Convert _id to id string
                if "_id" in doc:
                    doc["id"] = str(doc.pop("_id"))
                
                # Add trending metadata
                doc["trending_score"] = doc.get("trending_score", 0)
                doc["is_recent"] = doc.get("is_recent", False)
                
                products.append(doc)
            
            return products
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting trending products with scores: {e}")
            raise ErrorResponse("Database error during trending products retrieval", status_code=503)
    
    async def get_stats(self) -> Dict[str, int]:
        """Get product statistics for admin dashboard"""
        try:
            # Count all products (including inactive) for accurate dashboard stats
            total = await self.collection.count_documents({})
            active = await self.collection.count_documents({"is_active": True})
            
            # Product service only manages catalog data
            # Stock management is handled by inventory service
            return {
                "total": total,
                "active": active
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting stats: {e}")
            raise ErrorResponse("Database error during stats retrieval", status_code=503)
    
    async def check_sku_exists(self, sku: str, exclude_id: str = None) -> bool:
        """Check if SKU already exists (for duplicate validation)"""
        try:
            query = {"sku": sku, "is_active": True}
            if exclude_id and ObjectId.is_valid(exclude_id):
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            
            result = await self.collection.find_one(query)
            return result is not None
            
        except PyMongoError as e:
            logger.error(f"MongoDB error checking SKU: {e}")
            raise ErrorResponse("Database error during SKU validation", status_code=503)
    
    async def exists(self, product_id: str) -> bool:
        """Check if product exists and is active"""
        try:
            if not ObjectId.is_valid(product_id):
                return False
            
            result = await self.collection.find_one(
                {"_id": ObjectId(product_id), "is_active": True}
            )
            return result is not None
            
        except PyMongoError as e:
            logger.error(f"MongoDB error checking product existence: {e}")
            return False

    async def get_all_categories(self) -> List[str]:
        """Get all distinct categories from active products"""
        try:
            categories = await self.collection.distinct(
                "category",
                {"is_active": True, "category": {"$ne": None, "$ne": ""}}
            )
            return sorted(categories)
        except PyMongoError as e:
            logger.error(f"MongoDB error getting categories: {e}")
            raise ErrorResponse(f"Failed to fetch categories: {str(e)}", status_code=500)
