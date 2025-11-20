"""
Product service containing business logic layer
"""

import asyncio
from typing import List, Optional, Dict, Any

from app.core.errors import ErrorResponse
from app.core.logger import logger
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductStatsResponse
from app.events import event_publisher
from app.middleware.trace_context import get_trace_id


class ProductService:
    """Service layer for product business logic"""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def create_product(self, product_data: ProductCreate, created_by: str = "system") -> ProductResponse:
        """Create a new product with business validation"""
        # Validate business rules
        if product_data.price < 0:
            raise ErrorResponse("Price must be non-negative", status_code=400)
        
        # Check for duplicate SKU
        if product_data.sku:
            if await self.repository.check_sku_exists(product_data.sku):
                raise ErrorResponse("A product with this SKU already exists", status_code=400)
        
        # Create the product
        product = await self.repository.create(product_data, created_by)
        
        logger.info(
            f"Created product {product.id}",
            metadata={"event": "create_product", "product_id": product.id}
        )
        
        # Publish product.created event via Dapr
        await event_publisher.publish_product_created(
            product_id=product.id,
            product_data=product.model_dump(),
            created_by=created_by,
            correlation_id=get_trace_id()
        )
        
        return product
    
    async def get_product(self, product_id: str) -> ProductResponse:
        """Get product by ID"""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise ErrorResponse("Product not found", status_code=404)
        
        logger.info(
            f"Fetched product {product_id}",
            metadata={"event": "get_product", "product_id": product_id}
        )
        
        return product
    
    async def update_product(self, product_id: str, product_data: ProductUpdate, updated_by: str = None) -> ProductResponse:
        """Update product with business validation"""
        # Validate business rules
        if product_data.price is not None and product_data.price < 0:
            raise ErrorResponse("Price must be non-negative", status_code=400)
        
        # Check for duplicate SKU
        if product_data.sku:
            if await self.repository.check_sku_exists(product_data.sku, exclude_id=product_id):
                raise ErrorResponse("A product with this SKU already exists", status_code=400)
        
        # Update the product
        product = await self.repository.update(product_id, product_data, updated_by)
        if not product:
            raise ErrorResponse("Product not found", status_code=404)
        
        logger.info(
            f"Updated product {product_id}",
            metadata={"event": "update_product", "product_id": product_id}
        )
        
        # Publish product.updated event via Dapr
        await event_publisher.publish_product_updated(
            product_id=product_id,
            product_data=product.model_dump(),
            updated_by=updated_by or "system",
            correlation_id=get_trace_id()
        )
        
        return product
    
    async def delete_product(self, product_id: str, deleted_by: str = "system") -> None:
        """Soft delete a product"""
        success = await self.repository.delete(product_id)
        if not success:
            raise ErrorResponse("Product not found", status_code=404)
        
        logger.info(
            f"Soft deleted product {product_id}",
            metadata={"event": "soft_delete_product", "product_id": product_id}
        )
        
        # Publish product.deleted event via Dapr
        await event_publisher.publish_product_deleted(
            product_id=product_id,
            deleted_by=deleted_by,
            correlation_id=get_trace_id()
        )
    
    async def reactivate_product(self, product_id: str, updated_by: str = None) -> ProductResponse:
        """Reactivate a soft-deleted product"""
        # Get the product first to check SKU conflicts
        current_product = await self.repository.get_by_id(product_id)
        if not current_product:
            raise ErrorResponse("Product not found", status_code=404)
        
        if current_product.is_active:
            raise ErrorResponse("Product is already active", status_code=400)
        
        # Check for SKU conflicts if product has SKU
        if current_product.sku:
            if await self.repository.check_sku_exists(current_product.sku, exclude_id=product_id):
                raise ErrorResponse(
                    f"Cannot reactivate: Another active product already uses SKU '{current_product.sku}'",
                    status_code=400
                )
        
        # Reactivate the product
        product = await self.repository.reactivate(product_id, updated_by)
        
        logger.info(
            f"Reactivated product {product_id}",
            metadata={
                "event": "reactivate_product",
                "product_id": product_id,
                "reactivated_by": updated_by
            }
        )
        
        return product
    
    async def get_products(self,
                          search_text: str = None,
                          department: str = None,
                          category: str = None,
                          subcategory: str = None,
                          min_price: float = None,
                          max_price: float = None,
                          tags: List[str] = None,
                          skip: int = 0,
                          limit: int = None) -> Dict[str, Any]:
        """Get products with optional search and filters"""
        # If search_text is provided, perform search; otherwise, list products
        if search_text and search_text.strip():
            products, total_count = await self.repository.search(
                search_text, department, category, subcategory,
                min_price, max_price, tags, skip, limit
            )
            event_name = "search_products"
        else:
            products, total_count = await self.repository.list_products(
                department, category, subcategory,
                min_price, max_price, tags, skip, limit
            )
            event_name = "list_products"
        
        # Calculate pagination metadata
        if limit is not None and limit > 0:
            current_page = (skip // limit) + 1
            total_pages = (total_count + limit - 1) // limit
        else:
            current_page = 1
            total_pages = 1
        
        logger.info(
            f"Fetched {len(products)} products",
            metadata={
                "event": event_name,
                "count": len(products),
                "total": total_count,
                "search_text": search_text,
                "filters": {
                    "department": department,
                    "category": category,
                    "subcategory": subcategory,
                    "min_price": min_price,
                    "max_price": max_price,
                    "tags": tags,
                }
            }
        )
        
        # Convert ProductResponse objects to dicts for JSON serialization
        products_dict = [p.model_dump(mode='json') for p in products]
        
        return {
            "products": products_dict,
            "total_count": total_count,
            "current_page": current_page,
            "total_pages": total_pages
        }
    
    async def get_admin_stats(self) -> ProductStatsResponse:
        """Get product statistics for admin dashboard"""
        stats = await self.repository.get_stats()
        
        logger.info(
            "Product statistics fetched successfully",
            metadata={
                "event": "admin_stats_fetched",
                "stats": stats
            }
        )
        
        return ProductStatsResponse(**stats)
    
    async def get_trending_products_and_categories(
        self, 
        products_limit: int = 4, 
        categories_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get trending products and categories in a single call.
        Optimized for homepage display.
        
        Products include:
        - Full product details with review_aggregates
        - Trending score (pre-calculated)
        - Recency indicator
        
        Categories include:
        - Name, product count, ratings
        - Trending score
        """
        try:
            logger.info(
                "Fetching trending products and categories",
                metadata={
                    "event": "get_trending_products_and_categories",
                    "products_limit": products_limit,
                    "categories_limit": categories_limit
                }
            )
            
            # Fetch both in parallel
            products, categories = await asyncio.gather(
                self.repository.get_trending_products_with_scores(products_limit),
                self.repository.get_trending_categories(categories_limit)
            )
            
            logger.info(
                "Trending products and categories fetched successfully",
                metadata={
                    "event": "trending_data_fetched",
                    "products_count": len(products) if products else 0,
                    "categories_count": len(categories) if categories else 0
                }
            )
            
            return {
                "trending_products": products or [],
                "trending_categories": categories or []
            }
        except Exception as e:
            logger.error(
                f"Error fetching trending data: {str(e)}",
                metadata={
                    "event": "get_trending_data_error",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise ErrorResponse(
                f"Failed to fetch trending products and categories: {str(e)}", 
                status_code=500
            )
    
    async def get_all_categories(self) -> List[str]:
        """Get all distinct categories from active products"""
        logger.info("Fetching all categories", metadata={"event": "get_all_categories"})
        
        try:
            categories = await self.repository.get_all_categories()
            
            logger.info(
                f"Fetched {len(categories)} categories",
                metadata={"event": "categories_fetched", "count": len(categories)}
            )
            
            return categories
        except Exception as e:
            logger.error(
                f"Error fetching categories: {str(e)}",
                metadata={"event": "get_categories_error", "error": str(e)}
            )
            raise
    
    async def check_product_exists(self, product_id: str) -> Dict[str, bool]:
        """Check if product exists (for inter-service communication)"""
        exists = await self.repository.exists(product_id)
        return {"exists": exists}