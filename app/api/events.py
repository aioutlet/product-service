"""
Dapr Pub/Sub Subscription Endpoints
Handles incoming events from Dapr pub/sub
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from app.events.consumers.review_consumer import review_event_consumer
from app.events.consumers.inventory_consumer import inventory_event_consumer
from app.core.logger import logger

router = APIRouter(prefix="/dapr", tags=["dapr-pubsub"])


@router.get("/config")
async def get_dapr_config():
    """
    Dapr configuration endpoint.
    Returns app-level configuration for Dapr runtime.
    """
    return {
        "entities": [],
        "actorIdleTimeout": "1h",
        "actorScanInterval": "30s",
        "drainOngoingCallTimeout": "1m",
        "drainRebalancedActors": True
    }


@router.get("/subscribe")
async def get_subscriptions():
    """
    Dapr calls this endpoint to get list of subscriptions.
    Returns the topics this service wants to subscribe to.
    """
    subscriptions = [
        # Review service events - all published to review-events topic
        {
            "pubsubname": "review-pubsub",
            "topic": "review-events",
            "route": "/dapr/events/review.created",
            "match": "event.type == 'review.created'"
        },
        {
            "pubsubname": "review-pubsub",
            "topic": "review-events",
            "route": "/dapr/events/review.updated",
            "match": "event.type == 'review.updated'"
        },
        {
            "pubsubname": "review-pubsub",
            "topic": "review-events",
            "route": "/dapr/events/review.deleted",
            "match": "event.type == 'review.deleted'"
        },
        # Inventory service events (commented out until inventory service is ready)
        # {
        #     "pubsubname": "product-pubsub",
        #     "topic": "inventory.updated",
        #     "route": "/dapr/events/inventory.updated"
        # },
        # {
        #     "pubsubname": "product-pubsub",
        #     "topic": "inventory.low_stock",
        #     "route": "/dapr/events/inventory.low_stock"
        # }
    ]
    
    logger.info(
        "Dapr subscriptions configured",
        metadata={
            "subscriptionCount": len(subscriptions),
            "topics": [s["topic"] for s in subscriptions]
        }
    )
    
    return subscriptions


@router.post("/events/review.created")
async def handle_review_created(request: Request):
    """
    Handle review.created event from Dapr pub/sub.
    Called by Dapr when a review is created.
    """
    try:
        event_data = await request.json()
        
        logger.info(
            "Received review.created event",
            metadata={
                "correlationId": event_data.get("correlationId", "no-correlation"),
                "eventId": event_data.get("id"),
                "source": event_data.get("source")
            }
        )
        
        result = await review_event_consumer.handle_review_created(event_data)
        
        # Return success response for Dapr
        return {"status": "SUCCESS"}
        
    except Exception as e:
        logger.error(
            f"Error handling review.created event: {str(e)}",
            metadata={"error": str(e)}
        )
        # Still return success to avoid retries
        return {"status": "SUCCESS"}


@router.post("/events/review.updated")
async def handle_review_updated(request: Request):
    """
    Handle review.updated event from Dapr pub/sub.
    Called by Dapr when a review is updated.
    """
    try:
        event_data = await request.json()
        
        logger.info(
            "Received review.updated event",
            metadata={
                "correlationId": event_data.get("correlationId", "no-correlation"),
                "eventId": event_data.get("id")
            }
        )
        
        result = await review_event_consumer.handle_review_updated(event_data)
        
        return {"status": "SUCCESS"}
        
    except Exception as e:
        logger.error(
            f"Error handling review.updated event: {str(e)}",
            metadata={"error": str(e)}
        )
        return {"status": "SUCCESS"}


@router.post("/events/review.deleted")
async def handle_review_deleted(request: Request):
    """
    Handle review.deleted event from Dapr pub/sub.
    Called by Dapr when a review is deleted.
    """
    try:
        event_data = await request.json()
        
        logger.info(
            "Received review.deleted event",
            metadata={
                "correlationId": event_data.get("correlationId", "no-correlation"),
                "eventId": event_data.get("id")
            }
        )
        
        result = await review_event_consumer.handle_review_deleted(event_data)
        
        return {"status": "SUCCESS"}
        
    except Exception as e:
        logger.error(
            f"Error handling review.deleted event: {str(e)}",
            metadata={"error": str(e)}
        )
        return {"status": "SUCCESS"}
