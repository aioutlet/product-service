"""
Event Subscriptions Router
Handles Dapr Pub/Sub event consumption for product service.
Implements PRD REQ-3.2: Events Consumed (Inbound Integration)
Implements PRD REQ-5.2.2: Background worker for bulk import
"""
from fastapi import APIRouter, Request, BackgroundTasks

from src.services.review_aggregator import update_review_aggregates
from src.services.inventory_sync import update_availability_status
from src.services.badge_manager import evaluate_badge_criteria
from src.services.qa_sync import update_qa_stats
from src.services.dapr_publisher import get_dapr_publisher
from src.workers.bulk_import_worker import get_bulk_import_worker
from src.observability.logging import logger

router = APIRouter()


@router.post('/dapr/subscribe')
async def subscribe():
    """
    Dapr calls this endpoint to discover which events this service subscribes to.
    Returns array of subscription configurations.
    
    Implements: PRD REQ-3.2 - Event Consumption via Dapr Pub/Sub
    """
    subscriptions = [
        # Review events (REQ-3.2.1)
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'review.created',
            'route': '/events/review-created'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'review.updated',
            'route': '/events/review-updated'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'review.deleted',
            'route': '/events/review-deleted'
        },
        # Inventory events (REQ-3.2.2)
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'inventory.stock.updated',
            'route': '/events/inventory-updated'
        },
        # Analytics events (REQ-3.2.3)
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'analytics.product.sales.updated',
            'route': '/events/sales-updated'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'analytics.product.views.updated',
            'route': '/events/views-updated'
        },
        # Q&A events (REQ-3.2.4)
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'product.question.created',
            'route': '/events/question-created'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'product.answer.created',
            'route': '/events/answer-created'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'product.question.deleted',
            'route': '/events/question-deleted'
        },
        # Bulk import events (REQ-5.2.2)
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'product.bulk.import.job.created',
            'route': '/events/bulk-import-job-created'
        }
    ]
    return subscriptions


@router.post('/events/review-created')
async def handle_review_created(request: Request):
    """
    Handles review.created events from Review Service.
    Updates product rating aggregates (REQ-3.2.1).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        rating = event['data']['rating']
        verified = event['data'].get('verifiedPurchase', False)
        correlation_id = event.get('correlationId')

        # Update review aggregates (idempotent operation)
        await update_review_aggregates(
            product_id, 
            rating, 
            verified, 
            operation='add',
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process review.created event: {str(e)}",
            metadata={
                'event': 'review_created_handler_error',
                'error': str(e),
                'errorType': type(e).__name__
            }
        )
        return {'status': 'RETRY'}  # Dapr will retry this event


@router.post('/events/review-updated')
async def handle_review_updated(request: Request):
    """
    Handles review.updated events from Review Service.
    Re-calculates product rating aggregates (REQ-3.2.1).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        old_rating = event['data'].get('oldRating')
        new_rating = event['data']['rating']
        verified = event['data'].get('verifiedPurchase', False)
        correlation_id = event.get('correlationId')

        # Remove old rating and add new rating
        if old_rating:
            await update_review_aggregates(
                product_id, 
                old_rating, 
                verified, 
                operation='delete',
                correlation_id=correlation_id
            )
        
        await update_review_aggregates(
            product_id, 
            new_rating, 
            verified, 
            operation='add',
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process review.updated event: {str(e)}",
            metadata={
                'event': 'review_updated_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/review-deleted')
async def handle_review_deleted(request: Request):
    """
    Handles review.deleted events from Review Service.
    Recalculates product rating aggregates (REQ-3.2.1).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        rating = event['data']['rating']
        verified = event['data'].get('verifiedPurchase', False)
        correlation_id = event.get('correlationId')

        # Remove review from aggregates
        await update_review_aggregates(
            product_id, 
            rating, 
            verified, 
            operation='delete',
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process review.deleted event: {str(e)}",
            metadata={
                'event': 'review_deleted_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/inventory-updated')
async def handle_inventory_updated(request: Request):
    """
    Handles inventory.stock.updated events from Inventory Service.
    Updates product availability status (REQ-3.2.2).
    """
    try:
        event = await request.json()
        sku = event['data']['sku']
        product_id = event['data'].get('productId')
        available_qty = event['data']['availableQuantity']
        low_stock_threshold = event['data'].get('lowStockThreshold', 10)
        correlation_id = event.get('correlationId')

        # Update availability status (idempotent)
        was_out_of_stock = await update_availability_status(
            sku,
            product_id,
            available_qty,
            low_stock_threshold,
            correlation_id=correlation_id
        )

        # If product came back in stock, publish notification event
        if was_out_of_stock:
            publisher = get_dapr_publisher()
            await publisher.publish(
                'product.back.in.stock',
                {
                    'productId': product_id,
                    'sku': sku,
                    'availableQuantity': available_qty
                },
                correlation_id
            )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process inventory event: {str(e)}",
            metadata={
                'event': 'inventory_updated_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/sales-updated')
async def handle_sales_updated(request: Request):
    """
    Handles analytics.product.sales.updated events.
    Evaluates Best Seller badge criteria (REQ-3.2.3).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        category = event['data'].get('category')
        sales_last_30_days = event['data'].get('salesLast30Days', 0)
        category_rank = event['data'].get('categoryRank', 999)
        correlation_id = event.get('correlationId')

        # Evaluate badge criteria and auto-assign/remove
        await evaluate_badge_criteria(
            product_id,
            badge_type='best-seller',
            metrics={
                'category': category,
                'salesLast30Days': sales_last_30_days,
                'categoryRank': category_rank
            },
            criteria_threshold=100,  # Top 100 = Best Seller
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process sales event: {str(e)}",
            metadata={
                'event': 'sales_updated_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/views-updated')
async def handle_views_updated(request: Request):
    """
    Handles analytics.product.views.updated events.
    Evaluates Trending badge criteria (REQ-3.2.3).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        views_last_7_days = event['data'].get('viewsLast7Days', 0)
        views_prior_7_days = event['data'].get('viewsPrior7Days', 0)
        correlation_id = event.get('correlationId')

        # Calculate view growth percentage
        view_growth_pct = 0
        if views_prior_7_days > 0:
            view_growth_pct = \
                ((views_last_7_days - views_prior_7_days) / views_prior_7_days) * 100

        # Evaluate trending badge criteria
        await evaluate_badge_criteria(
            product_id,
            badge_type='trending',
            metrics={
                'viewsLast7Days': views_last_7_days,
                'viewsPrior7Days': views_prior_7_days,
                'viewGrowthPercent': view_growth_pct
            },
            criteria_threshold=50,  # 50% growth
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process views event: {str(e)}",
            metadata={
                'event': 'views_updated_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/question-created')
async def handle_question_created(request: Request):
    """
    Handles product.question.created events from Q&A Service.
    Updates product Q&A statistics (REQ-3.2.4).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        correlation_id = event.get('correlationId')

        # Update Q&A stats
        await update_qa_stats(
            product_id,
            operation='add',
            is_answer=False,
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process question.created event: {str(e)}",
            metadata={
                'event': 'question_created_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/answer-created')
async def handle_answer_created(request: Request):
    """
    Handles product.answer.created events from Q&A Service.
    Updates product Q&A statistics (REQ-3.2.4).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        correlation_id = event.get('correlationId')

        # Update Q&A stats (answer count)
        await update_qa_stats(
            product_id,
            operation='add',
            is_answer=True,
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process answer.created event: {str(e)}",
            metadata={
                'event': 'answer_created_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/question-deleted')
async def handle_question_deleted(request: Request):
    """
    Handles product.question.deleted events from Q&A Service.
    Updates product Q&A statistics (REQ-3.2.4).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        correlation_id = event.get('correlationId')

        # Update Q&A stats
        await update_qa_stats(
            product_id,
            operation='delete',
            is_answer=False,
            correlation_id=correlation_id
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to process question.deleted event: {str(e)}",
            metadata={
                'event': 'question_deleted_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}


@router.post('/events/bulk-import-job-created')
async def handle_bulk_import_job_created(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handles product.bulk.import.job.created events.
    Triggers background worker to process import job (REQ-5.2.2).
    """
    try:
        event = await request.json()
        job_id = event['data']['jobId']
        products = event['data'].get('products', [])
        import_mode = event['data'].get('importMode', 'partial')

        logger.info(
            f"Received bulk import job: {job_id}",
            metadata={
                'event': 'bulk_import_job_received',
                'jobId': job_id,
                'productCount': len(products),
                'importMode': import_mode
            }
        )

        # Get worker and schedule background processing
        worker = get_bulk_import_worker()

        # Process in background (non-blocking)
        background_tasks.add_task(
            worker.process_import_job,
            job_id,
            products,
            import_mode
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(
            f"Failed to handle bulk import job event: {str(e)}",
            metadata={
                'event': 'bulk_import_job_handler_error',
                'error': str(e)
            }
        )
        return {'status': 'RETRY'}
