"""
Inventory Synchronization Service
Handles inventory event consumption and maintains denormalized availability status.
Implements PRD REQ-3.2.2: Inventory Availability Synchronization
"""
from datetime import datetime, timezone
from typing import Optional
from src.db.mongodb import get_product_collection
from src.observability.logging import logger


async def update_availability_status(
    sku: str,
    product_id: Optional[str],
    available_quantity: int,
    low_stock_threshold: int = 10,
    correlation_id: Optional[str] = None
) -> bool:
    """
    Update product availability status based on inventory events (idempotent).
    
    Args:
        sku: Product SKU
        product_id: Optional product ID
        available_quantity: Current available quantity
        low_stock_threshold: Threshold for low stock warning
        correlation_id: Correlation ID for tracing
        
    Returns:
        bool: True if product was previously out of stock (for back-in-stock event)
        
    Implements:
        - REQ-3.2.2: Inventory Availability Synchronization
        - In Stock: quantity > 0
        - Low Stock: 0 < quantity <= threshold
        - Out of Stock: quantity = 0
    """
    try:
        collection = await get_product_collection()
        
        # Find product by SKU or product_id
        query = {}
        if product_id:
            query["_id"] = product_id
        elif sku:
            query["sku"] = sku
        else:
            logger.warning(
                "No product_id or SKU provided for inventory update",
                metadata={
                    'event': 'inventory_update_missing_identifier',
                    'correlationId': correlation_id
                }
            )
            return False
        
        product = await collection.find_one(query)
        if not product:
            logger.warning(
                f"Product not found for inventory update: SKU={sku}, ID={product_id}",
                metadata={
                    'event': 'inventory_update_product_not_found',
                    'sku': sku,
                    'productId': product_id,
                    'correlationId': correlation_id
                }
            )
            return False
        
        # Get current inventory status
        current_status = product.get('inventory_status', {})
        was_out_of_stock = current_status.get('availability') == 'out_of_stock'
        
        # Determine new availability status
        if available_quantity == 0:
            availability = 'out_of_stock'
        elif available_quantity <= low_stock_threshold:
            availability = 'low_stock'
        else:
            availability = 'in_stock'
        
        # Build updated inventory status
        inventory_status = {
            'availability': availability,
            'available_quantity': available_quantity,
            'low_stock_threshold': low_stock_threshold,
            'last_updated': datetime.now(timezone.utc)
        }
        
        # Update product in database (idempotent - upsert)
        await collection.update_one(
            {"_id": product.get('_id')},
            {"$set": {"inventory_status": inventory_status}},
            upsert=False
        )
        
        logger.info(
            "Updated inventory status for product",
            metadata={
                'event': 'inventory_status_updated',
                'productId': str(product.get('_id')),
                'sku': sku,
                'availability': availability,
                'availableQuantity': available_quantity,
                'wasOutOfStock': was_out_of_stock,
                'correlationId': correlation_id
            }
        )
        
        # Return whether product was out of stock (for back-in-stock event)
        return was_out_of_stock and available_quantity > 0
        
    except Exception as e:
        logger.error(
            f"Failed to update inventory status: {str(e)}",
            metadata={
                'event': 'inventory_update_error',
                'sku': sku,
                'productId': product_id,
                'error': str(e),
                'errorType': type(e).__name__,
                'correlationId': correlation_id
            }
        )
        raise
