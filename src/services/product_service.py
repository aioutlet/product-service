"""
Product service layer - business logic for product operations.

Handles business logic, validation, and orchestration between
repositories and external services.
"""

from typing import List, Optional, Tuple, Dict
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import PyMongoError
from motor.motor_asyncio import AsyncIOMotorCollection

from src.repositories.product_repository import ProductRepository
from src.core.logger import logger
from src.core.errors import ErrorResponse
from src.models.product import ProductCreate, ProductDB, ProductUpdate
from src.validators.product_validators import validate_object_id
from src.dependencies.auth import CurrentUser


class ProductService:
    """
    Service class for product business logic.
    
    Separates business logic from route handlers and data access.
    """
    
    def __init__(self, repository: ProductRepository):
        """
        Initialize product service.
        
        Args:
            repository: Product repository for data access
        """
        self.repository = repository
    
    async def get_product_by_id(
        self,
        product_id: str,
        correlation_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Get a product by ID.
        
        Args:
            product_id: Product ID
            correlation_id: Correlation ID for logging
            
        Returns:
            Product document or None if not found
            
        Raises:
            ErrorResponse: If ID is invalid
        """
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(product_id):
                raise ErrorResponse("Invalid product ID format", status_code=400)
            
            logger.debug(
                f"Fetching product by ID: {product_id}",
                correlation_id=correlation_id,
                metadata={"product_id": product_id}
            )
            
            product = await self.repository.find_by_id(product_id, correlation_id)
            
            if not product:
                logger.info(
                    f"Product not found: {product_id}",
                    correlation_id=correlation_id,
                    metadata={"product_id": product_id}
                )
            
            return product
        
        except Exception as e:
            logger.error(
                f"Error fetching product: {product_id}",
                correlation_id=correlation_id,
                error=e,
                metadata={"product_id": product_id}
            )
            raise
    
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
    ) -> Tuple[List[dict], int]:
        """
        Search products with filters.
        
        Args:
            search_text: Text to search
            department: Department filter
            category: Category filter
            subcategory: Subcategory filter
            min_price: Minimum price
            max_price: Maximum price
            tags: Tags filter
            skip: Records to skip
            limit: Max records to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (products list, total count)
            
        Raises:
            ErrorResponse: If search text is empty or invalid parameters
        """
        # Validate search text
        if not search_text or not search_text.strip():
            raise ErrorResponse("Search text cannot be empty", status_code=400)
        
        # Validate price range
        if min_price is not None and max_price is not None:
            if max_price < min_price:
                raise ErrorResponse(
                    "Maximum price must be greater than or equal to minimum price",
                    status_code=400
                )
        
        logger.info(
            f"Searching products: {search_text}",
            correlation_id=correlation_id,
            metadata={
                "search_text": search_text,
                "filters": {
                    "department": department,
                    "category": category,
                    "min_price": min_price,
                    "max_price": max_price
                }
            }
        )
        
        try:
            products, total_count = await self.repository.search_products(
                search_text=search_text,
                department=department,
                category=category,
                subcategory=subcategory,
                min_price=min_price,
                max_price=max_price,
                tags=tags,
                skip=skip,
                limit=limit,
                correlation_id=correlation_id
            )
            
            logger.info(
                f"Search completed: found {total_count} products",
                correlation_id=correlation_id,
                metadata={
                    "search_text": search_text,
                    "total_count": total_count,
                    "returned": len(products)
                }
            )
            
            return products, total_count
        
        except Exception as e:
            logger.error(
                "Error during product search",
                correlation_id=correlation_id,
                error=e,
                metadata={"search_text": search_text}
            )
            raise
    
    async def create_product(
        self,
        product_data: ProductCreate,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Create a new product.
        
        Args:
            product_data: Product creation request
            correlation_id: Correlation ID for logging
            
        Returns:
            Created product ID
            
        Raises:
            ErrorResponse: If SKU already exists or validation fails
        """
        logger.info(
            f"Creating product: {product_data.name}",
            correlation_id=correlation_id,
            metadata={"sku": product_data.sku, "name": product_data.name}
        )
        
        try:
            # Check SKU uniqueness
            is_unique = await self.repository.is_sku_unique(
                product_data.sku,
                correlation_id=correlation_id
            )
            
            if not is_unique:
                logger.warning(
                    f"SKU already exists: {product_data.sku}",
                    correlation_id=correlation_id,
                    metadata={"sku": product_data.sku}
                )
                raise ErrorResponse(
                    f"Product with SKU {product_data.sku} already exists",
                    status_code=409
                )
            
            # Convert to dict and add timestamps
            from datetime import datetime
            product_dict = product_data.dict()
            product_dict["created_at"] = datetime.utcnow()
            product_dict["updated_at"] = datetime.utcnow()
            
            # Create product
            product_id = await self.repository.create(product_dict, correlation_id)
            
            logger.info(
                f"Product created successfully: {product_id}",
                correlation_id=correlation_id,
                metadata={
                    "product_id": product_id,
                    "sku": product_data.sku,
                    "name": product_data.name
                }
            )
            
            return product_id
        
        except ErrorResponse:
            raise
        except Exception as e:
            logger.error(
                "Error creating product",
                correlation_id=correlation_id,
                error=e,
                metadata={"sku": product_data.sku}
            )
            raise
    
    async def get_active_products(
        self,
        skip: int = 0,
        limit: int = 10,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get all active products with pagination.
        
        Args:
            skip: Records to skip
            limit: Max records to return
            correlation_id: Correlation ID for logging
            
        Returns:
            Tuple of (products list, total count)
        """
        logger.debug(
            "Fetching active products",
            correlation_id=correlation_id,
            metadata={"skip": skip, "limit": limit}
        )
        
        try:
            products, total_count = await self.repository.get_active_products(
                skip=skip,
                limit=limit,
                correlation_id=correlation_id
            )
            
            logger.debug(
                f"Retrieved {len(products)} active products",
                correlation_id=correlation_id,
                metadata={"count": len(products), "total": total_count}
            )
            
            return products, total_count
        
        except Exception as e:
            logger.error(
                "Error fetching active products",
                correlation_id=correlation_id,
                error=e
            )
            raise
    
    async def update_product(
        self,
        product_id: str,
        product_data: dict,
        collection: AsyncIOMotorCollection,
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> ProductDB:
        """Update a product with change tracking."""
        try:
            # Validate admin permissions
            if acting_user and not acting_user.has_role("admin"):
                raise ErrorResponse("Admin access required", status_code=403)
            
            # Validate product ID
            obj_id = validate_object_id(product_id)
            
            # Extract only fields that were set
            update_data = {k: v for k, v in product_data.items() if v is not None}
            if not update_data:
                raise ErrorResponse("No fields to update", status_code=400)
            
            # Validate business rules
            if "price" in update_data and update_data["price"] < 0:
                raise ErrorResponse("Price must be non-negative.", status_code=400)
            
            # Check for duplicate SKU
            if "sku" in update_data:
                existing = await collection.find_one(
                    {"sku": update_data["sku"], "_id": {"$ne": obj_id}, "is_active": True}
                )
                if existing:
                    raise ErrorResponse("A product with this SKU already exists.", status_code=400)
            
            # Get current product for change tracking
            doc = await collection.find_one({"_id": obj_id})
            if not doc:
                raise ErrorResponse("Product not found", status_code=404)
            
            # Track history of changes
            changes = {k: v for k, v in update_data.items() if k in doc and doc[k] != v}
            if changes and acting_user:
                history_entry = {
                    "updated_by": acting_user.user_id,
                    "updated_at": datetime.now(timezone.utc),
                    "changes": changes,
                }
                update_data.setdefault("history", doc.get("history", [])).append(history_entry)
            
            # Add update timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Perform update
            await collection.update_one({"_id": obj_id}, {"$set": update_data})
            
            # Retrieve updated product
            doc = await collection.find_one({"_id": obj_id})
            updated_product = self._doc_to_model(doc)
            
            logger.info(
                f"Updated product {product_id}",
                correlation_id=correlation_id,
                metadata={"product_id": product_id, "changes": changes}
            )
            
            # Publish event
            await self._publish_product_updated(product_id, changes, acting_user, update_data)
            
            return updated_product
        
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Database connection error. Please try again later.", status_code=503)
    
    async def delete_product(
        self,
        product_id: str,
        collection: AsyncIOMotorCollection,
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ):
        """Soft delete a product."""
        try:
            # Validate admin permissions
            if acting_user and not acting_user.has_role("admin"):
                raise ErrorResponse("Admin access required", status_code=403)
            
            # Validate product ID
            obj_id = validate_object_id(product_id)
            
            # Check if product exists
            doc = await collection.find_one({"_id": obj_id})
            if not doc:
                raise ErrorResponse("Product not found", status_code=404)
            
            # Perform soft delete
            await collection.update_one(
                {"_id": obj_id},
                {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
            )
            
            logger.info(
                f"Soft deleted product {product_id}",
                correlation_id=correlation_id,
                metadata={"product_id": product_id}
            )
            
            # Publish event
            await self._publish_product_deleted(product_id, acting_user)
            
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Database connection error. Please try again later.", status_code=503)
    
    async def get_trending_products(
        self,
        collection: AsyncIOMotorCollection,
        limit: int = 4,
        correlation_id: Optional[str] = None
    ) -> List[ProductDB]:
        """Get trending products (simplified - returns recent active products)."""
        try:
            cursor = collection.find({"is_active": True}).sort("created_at", -1).limit(limit)
            products = [self._doc_to_model(doc) async for doc in cursor]
            
            logger.info(
                f"Fetched {len(products)} trending products",
                correlation_id=correlation_id,
                metadata={"count": len(products)}
            )
            
            return products
        
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}", correlation_id=correlation_id)
            raise ErrorResponse(f"Database error: {str(e)}", status_code=500)
    
    async def get_top_categories(
        self,
        collection: AsyncIOMotorCollection,
        limit: int = 5,
        correlation_id: Optional[str] = None
    ) -> List[dict]:
        """Get top categories by product count."""
        try:
            pipeline = [
                {"$match": {"is_active": True, "category": {"$exists": True, "$ne": None, "$ne": ""}}},
                {
                    "$group": {
                        "_id": "$category",
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
                {"$sort": {"product_count": -1}},
                {"$limit": limit},
                {"$project": {"_id": 0, "name": "$_id", "product_count": 1, "featured_product": 1}}
            ]
            
            cursor = collection.aggregate(pipeline)
            categories = [doc async for doc in cursor]
            
            logger.info(
                f"Fetched {len(categories)} trending categories",
                correlation_id=correlation_id,
                metadata={"count": len(categories)}
            )
            
            return categories
        
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}", correlation_id=correlation_id)
            raise ErrorResponse(f"Database error: {str(e)}", status_code=500)
    
    async def get_admin_stats(
        self,
        collection: AsyncIOMotorCollection,
        correlation_id: Optional[str] = None
    ) -> dict:
        """Get admin statistics."""
        try:
            total = await collection.count_documents({})
            active = await collection.count_documents({"is_active": True})
            
            stats = {
                "total": total,
                "active": active,
                "lowStock": 0,  # Handled by inventory service
                "outOfStock": 0  # Handled by inventory service
            }
            
            logger.info(
                "Product statistics fetched",
                correlation_id=correlation_id,
                metadata={"stats": stats}
            )
            
            return stats
        
        except PyMongoError as e:
            logger.error(f"Failed to fetch stats: {str(e)}", correlation_id=correlation_id)
            raise ErrorResponse("Database connection error. Please try again later.", status_code=503)
    
    async def list_products(
        self,
        collection: AsyncIOMotorCollection,
        department: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[ProductDB], int]:
        """List products with optional filters."""
        query = {}
        
        if department:
            query["department"] = department
        if category:
            query["category"] = category
        if subcategory:
            query["subcategory"] = subcategory
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
        if tags:
            query["tags"] = {"$in": tags}
        
        try:
            cursor = collection.find(query).skip(skip).limit(limit)
            products = await cursor.to_list(length=limit)
            total_count = await collection.count_documents(query)
            
            product_list = [self._doc_to_model(doc) for doc in products]
            
            logger.info(
                f"Listed {len(product_list)} products",
                correlation_id=correlation_id,
                metadata={"count": len(product_list), "total": total_count}
            )
            
            return product_list, total_count
        
        except PyMongoError as e:
            logger.error(f"Error listing products: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Failed to list products", status_code=500)
    
    async def reactivate_product(
        self,
        product_id: str,
        collection: AsyncIOMotorCollection,
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> ProductDB:
        """Reactivate a soft-deleted product."""
        try:
            if acting_user and not acting_user.has_role("admin"):
                raise ErrorResponse("Admin access required", status_code=403)
            
            obj_id = validate_object_id(product_id)
            
            doc = await collection.find_one({"_id": obj_id})
            if not doc:
                raise ErrorResponse("Product not found", status_code=404)
            
            if doc.get("is_active", True):
                raise ErrorResponse("Product is already active", status_code=400)
            
            # Check SKU uniqueness
            if doc.get("sku"):
                existing = await collection.find_one(
                    {"sku": doc["sku"], "_id": {"$ne": obj_id}, "is_active": True}
                )
                if existing:
                    raise ErrorResponse(
                        f"Cannot reactivate: Another active product already uses SKU '{doc['sku']}'",
                        status_code=400
                    )
            
            # Reactivate
            if acting_user:
                history_entry = {
                    "updated_by": acting_user.user_id,
                    "updated_at": datetime.now(timezone.utc),
                    "changes": {"is_active": True, "action": "reactivated"}
                }
                await collection.update_one(
                    {"_id": obj_id},
                    {
                        "$set": {"is_active": True, "updated_at": datetime.now(timezone.utc)},
                        "$push": {"history": history_entry}
                    }
                )
            else:
                await collection.update_one(
                    {"_id": obj_id},
                    {"$set": {"is_active": True, "updated_at": datetime.now(timezone.utc)}}
                )
            
            doc = await collection.find_one({"_id": obj_id})
            logger.info(
                f"Reactivated product {product_id}",
                correlation_id=correlation_id,
                metadata={"product_id": product_id}
            )
            
            return self._doc_to_model(doc)
        
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Database connection error. Please try again later.", status_code=503)
    
    def _doc_to_model(self, doc: dict) -> ProductDB:
        """Convert MongoDB document to ProductDB model."""
        return ProductDB(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            price=doc["price"],
            brand=doc.get("brand"),
            sku=doc.get("sku"),
            department=doc.get("department"),
            category=doc.get("category"),
            subcategory=doc.get("subcategory"),
            product_type=doc.get("productType"),
            images=doc.get("images", []),
            tags=doc.get("tags", []),
            colors=doc.get("colors", []),
            sizes=doc.get("sizes", []),
            specifications=doc.get("specifications", {}),
            created_by=doc.get("created_by", "system"),
            updated_by=doc.get("updated_by"),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
            is_active=doc.get("is_active", True),
            history=self._sanitize_history(doc.get("history", [])),
        )
    
    def _sanitize_history(self, history: list) -> list:
        """Remove problematic fields from history."""
        if not history:
            return []
        
        sanitized = []
        for entry in history:
            if isinstance(entry, dict) and "changes" in entry:
                changes = {k: v for k, v in entry["changes"].items() if k != "is_active"}
                sanitized.append({**entry, "changes": changes})
            else:
                sanitized.append(entry)
        
        return sanitized
    
    async def _publish_product_updated(
        self,
        product_id: str,
        changes: dict,
        acting_user: Optional[CurrentUser],
        update_data: dict
    ):
        """Publish product.updated event."""
        try:
            from src.services.dapr_publisher import get_dapr_publisher
            publisher = get_dapr_publisher()
            await publisher.publish(
                topic="product.updated",
                event_type="com.aioutlet.product.updated.v1",
                data={
                    "productId": product_id,
                    "changes": changes,
                    "updatedBy": acting_user.user_id if acting_user else None,
                    "updatedAt": update_data["updated_at"].isoformat()
                },
                correlation_id=None
            )
        except Exception as e:
            logger.error(f"Failed to publish product.updated event: {str(e)}")
    
    async def _publish_product_deleted(
        self,
        product_id: str,
        acting_user: Optional[CurrentUser]
    ):
        """Publish product.deleted event."""
        try:
            from src.services.dapr_publisher import get_dapr_publisher
            publisher = get_dapr_publisher()
            await publisher.publish(
                topic="product.deleted",
                event_type="com.aioutlet.product.deleted.v1",
                data={
                    "productId": product_id,
                    "hardDelete": False,
                    "deletedBy": acting_user.user_id if acting_user else None,
                    "deletedAt": datetime.now(timezone.utc).isoformat()
                },
                correlation_id=None
            )
        except Exception as e:
            logger.error(f"Failed to publish product.deleted event: {str(e)}")

    # ============= BULK OPERATIONS =============
    
    async def bulk_create(
        self,
        products: List[ProductCreate],
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> List[ProductDB]:
        """
        Create multiple products in batch.
        
        Args:
            products: List of products to create
            acting_user: User performing operation
            correlation_id: Request correlation ID
            
        Returns:
            List of created products
            
        Raises:
            ErrorResponse: If validation fails or SKUs are duplicated
        """
        # Validate admin permissions
        if not acting_user or not acting_user.has_role("admin"):
            raise ErrorResponse("Only admin users can create products.", status_code=403)
        
        # Check for duplicate SKUs in input
        skus = [p.sku for p in products if p.sku]
        if len(skus) != len(set(skus)):
            raise ErrorResponse("Duplicate SKUs in input.", status_code=400)
        
        # Check for existing SKUs in database
        existing = await self.repository.collection.find(
            {"sku": {"$in": skus}, "is_active": True}
        ).to_list(length=None)
        
        if existing:
            existing_skus = [e["sku"] for e in existing]
            raise ErrorResponse(f"SKUs already exist: {existing_skus}", status_code=400)
        
        # Prepare documents
        docs = []
        for product in products:
            if product.price < 0:
                raise ErrorResponse("Price must be non-negative.", status_code=400)
            
            data = product.model_dump()
            data["created_at"] = datetime.now(timezone.utc)
            data["updated_at"] = datetime.now(timezone.utc)
            data["is_active"] = True
            data["history"] = []
            docs.append(data)
        
        # Bulk insert
        result = await self.repository.collection.insert_many(docs)
        
        # Retrieve inserted documents
        inserted = await self.repository.collection.find(
            {"_id": {"$in": result.inserted_ids}}
        ).to_list(length=None)
        
        logger.info(
            f"Bulk created {len(result.inserted_ids)} products",
            correlation_id=correlation_id,
            metadata={"count": len(result.inserted_ids)}
        )
        
        return [ProductDB(**doc) for doc in inserted]
    
    async def bulk_update(
        self,
        updates: List[dict],
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> List[ProductDB]:
        """
        Update multiple products in batch.
        
        Args:
            updates: List of update operations (each with 'id' and fields)
            acting_user: User performing operation
            correlation_id: Request correlation ID
            
        Returns:
            List of updated products
            
        Raises:
            ErrorResponse: If user is not admin
        """
        if not acting_user or not acting_user.has_role("admin"):
            raise ErrorResponse("Only admin users can update products.", status_code=403)
        
        updated = []
        for upd in updates:
            product_id = upd.pop("id", None)
            if not product_id:
                continue
            
            product = ProductUpdate(**upd)
            
            try:
                updated_product = await self.update_product(
                    product_id,
                    product.model_dump(exclude_unset=True),
                    acting_user,
                    correlation_id
                )
                updated.append(updated_product)
            except ErrorResponse as e:
                logger.warning(
                    f"Bulk update failed for {product_id}: {e.detail}",
                    correlation_id=correlation_id
                )
                continue
        
        logger.info(
            f"Bulk updated {len(updated)} products",
            correlation_id=correlation_id,
            metadata={"count": len(updated)}
        )
        
        return updated
    
    async def bulk_delete(
        self,
        ids: List[str],
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Soft delete multiple products in batch.
        
        Args:
            ids: List of product IDs to delete
            acting_user: User performing operation
            correlation_id: Request correlation ID
            
        Returns:
            Dictionary with count of deleted products
            
        Raises:
            ErrorResponse: If user is not admin
        """
        if not acting_user or not acting_user.has_role("admin"):
            raise ErrorResponse("Only admin users can delete products.", status_code=403)
        
        deleted = 0
        for product_id in ids:
            try:
                await self.delete_product(
                    product_id,
                    acting_user,
                    correlation_id
                )
                deleted += 1
            except ErrorResponse as e:
                logger.warning(
                    f"Bulk delete failed for {product_id}: {e.detail}",
                    correlation_id=correlation_id
                )
                continue
        
        logger.info(
            f"Bulk soft deleted {deleted} products",
            correlation_id=correlation_id,
            metadata={"count": deleted}
        )
        
        return {"deleted": deleted}

    # ============= IMPORT/EXPORT OPERATIONS =============
    
    async def import_products(
        self,
        content: bytes,
        filetype: str,
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> list:
        """
        Import products from CSV or JSON file.
        
        Args:
            content: File content as bytes
            filetype: File format ("csv" or "json")
            acting_user: User performing import
            correlation_id: Request correlation ID
            
        Returns:
            List of imported products
            
        Raises:
            ErrorResponse: If file type unsupported or format invalid
        """
        import csv
        import io
        import json
        
        try:
            if filetype not in ["csv", "json"]:
                raise ErrorResponse(
                    "Unsupported file type. Only CSV and JSON are supported.",
                    status_code=400
                )
            
            products_data = []
            
            if filetype == "csv":
                content_str = content.decode("utf-8")
                csv_reader = csv.DictReader(io.StringIO(content_str))
                
                for row in csv_reader:
                    product_data = {
                        "name": row.get("name", "").strip(),
                        "description": row.get("description", "").strip(),
                        "price": float(row.get("price", 0)),
                        "category": row.get("category", "").strip(),
                        "brand": row.get("brand", "").strip(),
                        "sku": row.get("sku", "").strip(),
                        "tags": [tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()],
                        "images": [img.strip() for img in row.get("images", "").split(",") if img.strip()],
                        "attributes": json.loads(row.get("attributes", "{}")) if row.get("attributes") else {}
                    }
                    
                    if not product_data["name"] or product_data["price"] < 0:
                        logger.warning(
                            f"Invalid product data in CSV: {product_data}",
                            correlation_id=correlation_id
                        )
                        continue
                    
                    products_data.append(product_data)
            
            elif filetype == "json":
                content_str = content.decode("utf-8")
                json_data = json.loads(content_str)
                
                if isinstance(json_data, list):
                    products_data = json_data
                else:
                    raise ErrorResponse("JSON file must contain an array of products.", status_code=400)
            
            if not products_data:
                raise ErrorResponse("No valid products found in the file.", status_code=400)
            
            # Import products
            imported_products = []
            for product_data in products_data:
                try:
                    # Check for duplicate SKU
                    if product_data.get("sku"):
                        existing = await self.repository.collection.find_one(
                            {"sku": product_data["sku"], "is_active": True}
                        )
                        if existing:
                            logger.warning(
                                f"Skipping duplicate SKU: {product_data['sku']}",
                                correlation_id=correlation_id
                            )
                            continue
                    
                    # Add metadata
                    product_data["created_at"] = datetime.now(timezone.utc)
                    product_data["updated_at"] = datetime.now(timezone.utc)
                    product_data["is_active"] = True
                    product_data["history"] = []
                    product_data["created_by"] = acting_user.user_id if acting_user else "system"
                    
                    # Insert
                    result = await self.repository.collection.insert_one(product_data)
                    doc = await self.repository.collection.find_one({"_id": result.inserted_id})
                    imported_products.append(ProductDB(**doc))
                
                except Exception as e:
                    logger.error(
                        f"Error importing product: {e}",
                        correlation_id=correlation_id,
                        metadata={"product": product_data}
                    )
                    continue
            
            logger.info(
                f"Imported {len(imported_products)} products",
                correlation_id=correlation_id,
                metadata={"count": len(imported_products)}
            )
            
            return imported_products
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Invalid JSON format in file.", status_code=400)
        except UnicodeDecodeError as e:
            logger.error(f"File encoding error: {e}", correlation_id=correlation_id)
            raise ErrorResponse(
                "File encoding error. Please ensure the file is UTF-8 encoded.",
                status_code=400
            )
        except PyMongoError as e:
            logger.error(f"MongoDB error during import: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Database connection error. Please try again later.", status_code=503)
    
    async def export_products(
        self,
        filetype: str = "json",
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Export products in JSON or CSV format.
        
        Args:
            filetype: Export format ("json" or "csv")
            correlation_id: Request correlation ID
            
        Returns:
            Exported product data as string
            
        Raises:
            ErrorResponse: If file type unsupported or database error
        """
        import csv
        import io
        import json
        
        try:
            if filetype not in ["csv", "json"]:
                raise ErrorResponse(
                    "Unsupported export type. Only CSV and JSON are supported.",
                    status_code=400
                )
            
            # Fetch active products
            cursor = self.repository.collection.find({"is_active": True})
            products = []
            
            async for doc in cursor:
                products.append(doc)
            
            logger.info(
                f"Found {len(products)} products to export",
                correlation_id=correlation_id,
                metadata={"count": len(products)}
            )
            
            if filetype == "json":
                for product in products:
                    product["_id"] = str(product["_id"])
                    if isinstance(product.get("created_at"), datetime):
                        product["created_at"] = product["created_at"].isoformat()
                    if isinstance(product.get("updated_at"), datetime):
                        product["updated_at"] = product["updated_at"].isoformat()
                    
                    if "history" in product and isinstance(product["history"], list):
                        for history_entry in product["history"]:
                            if isinstance(history_entry.get("updated_at"), datetime):
                                history_entry["updated_at"] = history_entry["updated_at"].isoformat()
                
                return json.dumps(products, indent=2)
            
            elif filetype == "csv":
                output = io.StringIO()
                if products:
                    headers = [
                        "id", "name", "description", "price", "category", "brand",
                        "sku", "tags", "images", "attributes", "created_by",
                        "created_at", "updated_at"
                    ]
                    
                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()
                    
                    for product in products:
                        row = {
                            "id": str(product["_id"]),
                            "name": product.get("name", ""),
                            "description": product.get("description", ""),
                            "price": product.get("price", 0),
                            "category": product.get("category", ""),
                            "brand": product.get("brand", ""),
                            "sku": product.get("sku", ""),
                            "tags": ",".join(product.get("tags", [])),
                            "images": ",".join(product.get("images", [])),
                            "attributes": json.dumps(product.get("attributes", {})),
                            "created_by": product.get("created_by", ""),
                            "created_at": (
                                product.get("created_at").isoformat()
                                if isinstance(product.get("created_at"), datetime)
                                else str(product.get("created_at", ""))
                            ),
                            "updated_at": (
                                product.get("updated_at").isoformat()
                                if isinstance(product.get("updated_at"), datetime)
                                else str(product.get("updated_at", ""))
                            )
                        }
                        writer.writerow(row)
                
                return output.getvalue()
            
            logger.info(
                f"Exported {len(products)} products as {filetype}",
                correlation_id=correlation_id,
                metadata={"count": len(products), "format": filetype}
            )
        
        except ErrorResponse:
            raise
        except PyMongoError as e:
            logger.error(f"MongoDB error during export: {e}", correlation_id=correlation_id)
            raise ErrorResponse("Database connection error. Please try again later.", status_code=503)
        except Exception as e:
            logger.error(f"Unexpected error during export: {e}", correlation_id=correlation_id)
            raise ErrorResponse("An unexpected error occurred during export.", status_code=500)
