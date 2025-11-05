"""
Bulk Operations Service - Handles batch operations on products.

This service manages bulk create, update, and delete operations
for products, providing efficient batch processing capabilities.
"""

from typing import List, Optional
from datetime import datetime, timezone

from src.repositories.product_repository import ProductRepository
from src.core.logger import logger
from src.core.errors import ErrorResponse
from src.models.product import ProductCreate, ProductDB, ProductUpdate
from src.dependencies.auth import CurrentUser


class BulkOperationsService:
    """Service for bulk product operations."""
    
    def __init__(self, repository: ProductRepository):
        """
        Initialize bulk operations service.
        
        Args:
            repository: Product repository for data access
        """
        self.repository = repository
    
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
        product_service,  # Injected ProductService for individual updates
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> List[ProductDB]:
        """
        Update multiple products in batch.
        
        Args:
            updates: List of update operations (each with 'id' and fields)
            product_service: ProductService instance for individual updates
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
                updated_product = await product_service.update_product(
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
        
        # Soft delete (set is_active = False)
        result = await self.repository.collection.update_many(
            {"_id": {"$in": [self.repository._to_object_id(pid) for pid in ids]}},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc),
                    "deleted_at": datetime.now(timezone.utc),
                    "deleted_by": acting_user.user_id if acting_user else None
                }
            }
        )
        
        deleted = result.modified_count
        
        logger.info(
            f"Bulk deleted {deleted} products",
            correlation_id=correlation_id,
            metadata={"count": deleted}
        )
        
        return {"deleted": deleted}
    
    async def bulk_activate(
        self,
        ids: List[str],
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Activate multiple products in batch.
        
        Args:
            ids: List of product IDs to activate
            acting_user: User performing operation
            correlation_id: Request correlation ID
            
        Returns:
            Dictionary with count of activated products
            
        Raises:
            ErrorResponse: If user is not admin
        """
        if not acting_user or not acting_user.has_role("admin"):
            raise ErrorResponse("Only admin users can activate products.", status_code=403)
        
        result = await self.repository.collection.update_many(
            {"_id": {"$in": [self.repository._to_object_id(pid) for pid in ids]}},
            {
                "$set": {
                    "is_active": True,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$unset": {
                    "deleted_at": "",
                    "deleted_by": ""
                }
            }
        )
        
        activated = result.modified_count
        
        logger.info(
            f"Bulk activated {activated} products",
            correlation_id=correlation_id,
            metadata={"count": activated}
        )
        
        return {"activated": activated}
    
    async def bulk_deactivate(
        self,
        ids: List[str],
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Deactivate multiple products in batch.
        
        Args:
            ids: List of product IDs to deactivate
            acting_user: User performing operation
            correlation_id: Request correlation ID
            
        Returns:
            Dictionary with count of deactivated products
            
        Raises:
            ErrorResponse: If user is not admin
        """
        if not acting_user or not acting_user.has_role("admin"):
            raise ErrorResponse("Only admin users can deactivate products.", status_code=403)
        
        result = await self.repository.collection.update_many(
            {"_id": {"$in": [self.repository._to_object_id(pid) for pid in ids]}},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        deactivated = result.modified_count
        
        logger.info(
            f"Bulk deactivated {deactivated} products",
            correlation_id=correlation_id,
            metadata={"count": deactivated}
        )
        
        return {"deactivated": deactivated}
