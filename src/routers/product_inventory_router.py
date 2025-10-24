"""
Product with Inventory Router

This router demonstrates how to aggregate product data from the product-service
with inventory data from the inventory-service, following microservices best practices.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.controllers.product_controller import get_all_products, get_product_by_id
from src.core.logger import get_logger
from src.db.mongodb import get_database
from src.services.inventory_client import InventoryItem, get_inventory_client

logger = get_logger(__name__)

router = APIRouter(prefix="/products", tags=["products-with-inventory"])


class ProductWithInventory(BaseModel):
    """Product model enriched with inventory information."""

    # Product data (from product-service)
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    images: List[str] = []
    tags: List[str] = []
    is_active: bool = True

    # Inventory data (from inventory-service)
    inventory: Optional[InventoryItem] = None
    in_stock: bool = False
    available_quantity: int = 0


@router.get("/{product_id}/with-inventory", response_model=ProductWithInventory)
async def get_product_with_inventory(product_id: str, db=Depends(get_database)):
    """
    Get a product with its inventory information.

    This endpoint demonstrates the Frontend Aggregation pattern where
    the API aggregates data from multiple microservices.

    Args:
        product_id: Product ID
        db: MongoDB database connection

    Returns:
        ProductWithInventory: Product data enriched with inventory information
    """
    try:
        # Get product data from product-service (local call)
        product = await get_product_by_id(product_id, db["products"])

        # Get inventory data from inventory-service (remote call)
        inventory_client = get_inventory_client()
        inventory = None
        in_stock = False
        available_quantity = 0

        if product.sku:
            try:
                inventory = await inventory_client.get_inventory_by_sku(product.sku)
                if inventory:
                    in_stock = inventory.quantity_available > 0
                    available_quantity = inventory.quantity_available
            except Exception as e:
                logger.warning(f"Could not fetch inventory for SKU {product.sku}: {e}")
                # Continue without inventory data - graceful degradation

        return ProductWithInventory(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            sku=product.sku,
            images=product.images,
            tags=product.tags,
            is_active=product.is_active,
            inventory=inventory,
            in_stock=in_stock,
            available_quantity=available_quantity,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product with inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/with-inventory", response_model=List[ProductWithInventory])
async def get_products_with_inventory(
    limit: int = 10,
    skip: int = 0,
    category: Optional[str] = None,
    active_only: bool = True,
    db=Depends(get_database),
):
    """
    Get multiple products with their inventory information.

    This endpoint demonstrates batch aggregation of data from multiple microservices.

    Args:
        limit: Maximum number of products to return
        skip: Number of products to skip
        category: Filter by category
        active_only: Only return active products
        db: MongoDB database connection

    Returns:
        List[ProductWithInventory]: List of products enriched with inventory information
    """
    try:
        # Get products from product-service (local call)
        products = await get_all_products(
            db["products"], limit, skip, category, active_only
        )

        if not products:
            return []

        # Get inventory data for all products in batch
        inventory_client = get_inventory_client()
        skus = [product.sku for product in products if product.sku]

        inventory_map = {}
        if skus:
            try:
                inventory_items = await inventory_client.get_multiple_inventory(skus)
                inventory_map = {item.sku: item for item in inventory_items}
            except Exception as e:
                logger.warning(f"Could not fetch inventory data in batch: {e}")
                # Continue without inventory data - graceful degradation

        # Combine product and inventory data
        enriched_products = []
        for product in products:
            inventory = inventory_map.get(product.sku) if product.sku else None
            in_stock = inventory.quantity_available > 0 if inventory else False
            available_quantity = inventory.quantity_available if inventory else 0

            enriched_products.append(
                ProductWithInventory(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    category=product.category,
                    brand=product.brand,
                    sku=product.sku,
                    images=product.images,
                    tags=product.tags,
                    is_active=product.is_active,
                    inventory=inventory,
                    in_stock=in_stock,
                    available_quantity=available_quantity,
                )
            )

        return enriched_products

    except Exception as e:
        logger.error(f"Error getting products with inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}/stock-check")
async def check_product_stock(
    product_id: str, quantity: int = 1, db=Depends(get_database)
):
    """
    Check if a specific quantity of a product is available.

    Args:
        product_id: Product ID
        quantity: Quantity to check
        db: MongoDB database connection

    Returns:
        dict: Stock availability information
    """
    try:
        # Get product to get SKU
        product = await get_product_by_id(product_id, db["products"])

        if not product.sku:
            raise HTTPException(status_code=400, detail="Product has no SKU")

        # Check stock with inventory service
        inventory_client = get_inventory_client()
        available = await inventory_client.is_sku_available(product.sku, quantity)

        return {
            "product_id": product_id,
            "sku": product.sku,
            "requested_quantity": quantity,
            "available": available,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking stock for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
