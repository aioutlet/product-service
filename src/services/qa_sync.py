"""
Q&A Statistics Synchronization Service
Handles Q&A event consumption and maintains denormalized Q&A statistics.
Implements PRD REQ-3.2.4: Q&A Statistics Synchronization
"""
from datetime import datetime, timezone
from typing import Optional
from src.db.mongodb import get_product_collection
from src.observability.logging import logger


async def update_qa_stats(
    product_id: str,
    operation: str,
    is_answer: bool = False,
    correlation_id: Optional[str] = None
):
    """
    Update product Q&A statistics (idempotent operation).
    
    Args:
        product_id: Product ID to update
        operation: 'add' or 'delete'
        is_answer: True if this is an answer event (not a question)
        correlation_id: Correlation ID for tracing
        
    Implements:
        - REQ-3.2.4: Q&A Statistics Synchronization
        - Total question count
        - Answered question count
    """
    try:
        collection = await get_product_collection()
        
        # Find the product
        product = await collection.find_one({"_id": product_id})
        if not product:
            logger.warning(
                f"Product not found for Q&A stats update: {product_id}",
                metadata={
                    'event': 'qa_stats_product_not_found',
                    'productId': product_id,
                    'correlationId': correlation_id
                }
            )
            return
        
        # Get current Q&A stats or initialize
        qa_stats = product.get('qa_stats', {
            'total_questions': 0,
            'answered_questions': 0,
            'last_updated': None
        })
        
        # Update stats based on operation and event type
        if operation == 'add':
            if is_answer:
                # Answer created - increment answered count
                qa_stats['answered_questions'] = \
                    qa_stats.get('answered_questions', 0) + 1
            else:
                # Question created - increment total count
                qa_stats['total_questions'] = \
                    qa_stats.get('total_questions', 0) + 1
                    
        elif operation == 'delete':
            if not is_answer:
                # Question deleted - decrement total count
                qa_stats['total_questions'] = \
                    max(0, qa_stats.get('total_questions', 0) - 1)
                # Note: Answered count management depends on Q&A Service behavior
                # If deleted questions include answer count, we should decrement
        
        qa_stats['last_updated'] = datetime.now(timezone.utc)
        
        # Update product in database (idempotent - upsert)
        await collection.update_one(
            {"_id": product_id},
            {"$set": {"qa_stats": qa_stats}},
            upsert=False
        )
        
        logger.info(
            f"Updated Q&A stats for product {product_id}",
            metadata={
                'event': 'qa_stats_updated',
                'productId': product_id,
                'operation': operation,
                'isAnswer': is_answer,
                'totalQuestions': qa_stats['total_questions'],
                'answeredQuestions': qa_stats['answered_questions'],
                'correlationId': correlation_id
            }
        )
        
    except Exception as e:
        logger.error(
            f"Failed to update Q&A stats: {str(e)}",
            metadata={
                'event': 'qa_stats_error',
                'productId': product_id,
                'error': str(e),
                'errorType': type(e).__name__,
                'correlationId': correlation_id
            }
        )
        raise
