"""
Review Created Handler
Updates product rating when a new review is created
"""
from src.shared.observability import logger
from src.shared.db.database import get_database

async def handle_review_created(event_data: dict, correlation_id: str = None):
    """
    Handle review.created event
    Updates product's average rating and review count
    
    Args:
        event_data: Event data containing productId, rating
        correlation_id: Correlation ID for tracing
    """
    try:
        product_id = event_data.get('productId')
        rating = event_data.get('rating')
        
        if not product_id or rating is None:
            logger.warning("review.created event missing productId or rating", metadata={
                "correlationId": correlation_id,
                "eventData": event_data
            })
            return
        
        db = await get_database()
        products_collection = db['products']
        
        # Get current product to recalculate average
        product = await products_collection.find_one({'_id': product_id})
        
        if not product:
            logger.warning(f"Product {product_id} not found", metadata={
                "correlationId": correlation_id,
                "productId": product_id
            })
            return
        
        # Calculate new average rating
        current_avg = product.get('averageRating', 0)
        review_count = product.get('reviewCount', 0)
        
        new_review_count = review_count + 1
        new_avg = ((current_avg * review_count) + rating) / new_review_count
        
        # Update product with new rating
        result = await products_collection.update_one(
            {'_id': product_id},
            {
                '$set': {
                    'averageRating': round(new_avg, 2),
                    'reviewCount': new_review_count
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated rating for product {product_id}", metadata={
                "correlationId": correlation_id,
                "productId": product_id,
                "newRating": round(new_avg, 2),
                "reviewCount": new_review_count
            })
        
    except Exception as e:
        logger.error(f"Error handling review.created event: {str(e)}", metadata={
            "correlationId": correlation_id,
            "error": str(e),
            "eventData": event_data
        })
        raise
