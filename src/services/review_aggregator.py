"""
Review Aggregator Service
Handles review event consumption and maintains denormalized review aggregates.
Implements PRD REQ-3.2.1: Review Data Synchronization
"""
from typing import Optional
from src.db.mongodb import get_product_collection
from src.observability.logging import logger


async def update_review_aggregates(
    product_id: str,
    rating: int,
    verified_purchase: bool = False,
    operation: str = 'add',
    correlation_id: Optional[str] = None
):
    """
    Update product review aggregates (idempotent operation).
    
    Args:
        product_id: Product ID to update
        rating: Rating value (1-5)
        verified_purchase: Whether the review is from a verified purchase
        operation: 'add', 'update', or 'delete'
        correlation_id: Correlation ID for tracing
        
    Implements:
        - REQ-3.2.1: Review Data Synchronization
        - Average rating calculation
        - Total review count
        - Rating distribution
        - Verified purchase count
    """
    try:
        collection = await get_product_collection()
        
        # Find the product
        product = await collection.find_one({"_id": product_id})
        if not product:
            logger.warning(
                f"Product not found for review aggregate update: {product_id}",
                metadata={
                    'event': 'review_aggregate_product_not_found',
                    'productId': product_id,
                    'correlationId': correlation_id
                }
            )
            return
        
        # Get current aggregates or initialize
        aggregates = product.get('review_aggregates', {
            'average_rating': 0.0,
            'total_reviews': 0,
            'verified_purchase_count': 0,
            'rating_distribution': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
        })
        
        # Update aggregates based on operation
        if operation == 'add':
            # Add new review
            total = aggregates['total_reviews']
            current_avg = aggregates['average_rating']
            
            # Calculate new average using incremental formula
            new_total = total + 1
            new_avg = ((current_avg * total) + rating) / new_total
            
            aggregates['average_rating'] = round(new_avg, 2)
            aggregates['total_reviews'] = new_total
            aggregates['rating_distribution'][str(rating)] = \
                aggregates['rating_distribution'].get(str(rating), 0) + 1
            
            if verified_purchase:
                aggregates['verified_purchase_count'] = \
                    aggregates.get('verified_purchase_count', 0) + 1
                    
        elif operation == 'delete':
            # Remove review
            total = aggregates['total_reviews']
            if total > 0:
                current_avg = aggregates['average_rating']
                
                # Recalculate average
                new_total = total - 1
                if new_total > 0:
                    new_avg = ((current_avg * total) - rating) / new_total
                    aggregates['average_rating'] = round(new_avg, 2)
                else:
                    aggregates['average_rating'] = 0.0
                
                aggregates['total_reviews'] = new_total
                aggregates['rating_distribution'][str(rating)] = \
                    max(0, aggregates['rating_distribution'].get(str(rating), 0) - 1)
                
                if verified_purchase:
                    aggregates['verified_purchase_count'] = \
                        max(0, aggregates.get('verified_purchase_count', 0) - 1)
        
        # Update product in database (idempotent - upsert)
        await collection.update_one(
            {"_id": product_id},
            {"$set": {"review_aggregates": aggregates}},
            upsert=False
        )
        
        logger.info(
            f"Updated review aggregates for product {product_id}",
            metadata={
                'event': 'review_aggregates_updated',
                'productId': product_id,
                'operation': operation,
                'rating': rating,
                'newAverage': aggregates['average_rating'],
                'totalReviews': aggregates['total_reviews'],
                'correlationId': correlation_id
            }
        )
        
    except Exception as e:
        logger.error(
            f"Failed to update review aggregates: {str(e)}",
            metadata={
                'event': 'review_aggregates_error',
                'productId': product_id,
                'error': str(e),
                'errorType': type(e).__name__,
                'correlationId': correlation_id
            }
        )
        raise
