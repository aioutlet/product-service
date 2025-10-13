"""
Order Completed Handler
Updates product purchase count when an order is completed
"""
from src.shared.observability import logger
from src.shared.db.database import get_database

async def handle_order_completed(event_data: dict, correlation_id: str = None):
    """
    Handle order.completed event
    Updates purchase count for products in the order
    
    Args:
        event_data: Event data containing orderId and items
        correlation_id: Correlation ID for tracing
    """
    try:
        order_id = event_data.get('orderId')
        items = event_data.get('items', [])
        
        if not items:
            logger.warning(f"Order {order_id} has no items", metadata={
                "correlationId": correlation_id,
                "orderId": order_id
            })
            return
        
        db = await get_database()
        products_collection = db['products']
        
        # Update purchase count for each product
        for item in items:
            product_id = item.get('productId')
            quantity = item.get('quantity', 1)
            
            if product_id:
                result = await products_collection.update_one(
                    {'_id': product_id},
                    {'$inc': {'purchaseCount': quantity}}
                )
                
                if result.modified_count > 0:
                    logger.info(f"Updated purchase count for product {product_id}", metadata={
                        "correlationId": correlation_id,
                        "productId": product_id,
                        "quantity": quantity,
                        "orderId": order_id
                    })
                else:
                    logger.warning(f"Product {product_id} not found", metadata={
                        "correlationId": correlation_id,
                        "productId": product_id,
                        "orderId": order_id
                    })
        
        logger.info(f"Processed order completion for {len(items)} products", metadata={
            "correlationId": correlation_id,
            "orderId": order_id,
            "itemCount": len(items)
        })
        
    except Exception as e:
        logger.error(f"Error handling order.completed event: {str(e)}", metadata={
            "correlationId": correlation_id,
            "error": str(e),
            "eventData": event_data
        })
        raise
