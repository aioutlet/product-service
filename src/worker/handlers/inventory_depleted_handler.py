"""
Inventory Depleted Handler
Marks product as out of stock when inventory is depleted
"""
from src.shared.observability import logger
from src.shared.db.database import get_database

async def handle_inventory_depleted(event_data: dict, correlation_id: str = None):
    """
    Handle inventory.depleted event
    Marks product as out of stock
    
    Args:
        event_data: Event data containing productId
        correlation_id: Correlation ID for tracing
    """
    try:
        product_id = event_data.get('productId')
        
        if not product_id:
            logger.warning("inventory.depleted event missing productId", metadata={
                "correlationId": correlation_id,
                "eventData": event_data
            })
            return
        
        db = await get_database()
        products_collection = db['products']
        
        # Mark product as out of stock
        result = await products_collection.update_one(
            {'_id': product_id},
            {
                '$set': {
                    'inStock': False,
                    'stockStatus': 'out_of_stock'
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Marked product {product_id} as out of stock", metadata={
                "correlationId": correlation_id,
                "productId": product_id
            })
        else:
            logger.warning(f"Product {product_id} not found or already out of stock", metadata={
                "correlationId": correlation_id,
                "productId": product_id
            })
        
    except Exception as e:
        logger.error(f"Error handling inventory.depleted event: {str(e)}", metadata={
            "correlationId": correlation_id,
            "error": str(e),
            "eventData": event_data
        })
        raise
