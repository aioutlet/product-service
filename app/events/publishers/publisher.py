"""
Dapr Event Publisher for Product Service
Publishes events via Dapr pub/sub component
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from dapr.clients import DaprClient
    DAPR_AVAILABLE = True
except ImportError:
    DAPR_AVAILABLE = False

from app.core.config import config
from app.core.logger import logger
from app.middleware.correlation_id import get_correlation_id


class DaprEventPublisher:
    """
    Publisher for sending events via Dapr pub/sub.
    Handles product lifecycle events for event-driven architecture.
    """
    
    def __init__(self):
        self.pubsub_name = "product-pubsub"
        self.service_name = config.service_name
        
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish an event via Dapr pub/sub.
        
        Args:
            event_type: Type of event (e.g., 'product.created', 'product.updated')
            data: Event data payload
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            True if successful, False otherwise
        """
        if not DAPR_AVAILABLE:
            logger.warning(
                "Dapr SDK not available. Event publishing disabled.",
                metadata={"event_type": event_type}
            )
            return False
        
        # Get correlation ID from context if not provided
        if not correlation_id:
            correlation_id = get_correlation_id()
        
        # Construct event payload
        event_payload = {
            "specversion": "1.0",
            "type": event_type,
            "source": self.service_name,
            "id": correlation_id or f"{event_type}-{datetime.utcnow().timestamp()}",
            "time": datetime.utcnow().isoformat() + "Z",
            "datacontenttype": "application/json",
            "data": data,
            "correlationId": correlation_id
        }
        
        try:
            # Publish via Dapr
            with DaprClient() as client:
                client.publish_event(
                    pubsub_name=self.pubsub_name,
                    topic_name=event_type,
                    data=json.dumps(event_payload),
                    data_content_type="application/json"
                )
            
            logger.info(
                f"Published event: {event_type}",
                metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type,
                    "source": self.service_name,
                    "transport": "dapr"
                }
            )
            return True
            
        except Exception as e:
            # Log error but don't fail the operation
            # Events are best-effort delivery
            logger.error(
                f"Failed to publish event: {event_type}",
                metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type,
                    "error": str(e),
                    "transport": "dapr"
                }
            )
            return False
    
    async def publish_product_created(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        created_by: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Publish product.created event"""
        data = {
            "productId": product_id,
            "product": product_data,
            "createdBy": created_by,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return await self.publish_event("product.created", data, correlation_id)
    
    async def publish_product_updated(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        updated_by: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Publish product.updated event"""
        data = {
            "productId": product_id,
            "product": product_data,
            "updatedBy": updated_by,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return await self.publish_event("product.updated", data, correlation_id)
    
    async def publish_product_deleted(
        self,
        product_id: str,
        deleted_by: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Publish product.deleted event"""
        data = {
            "productId": product_id,
            "deletedBy": deleted_by,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return await self.publish_event("product.deleted", data, correlation_id)


# Global publisher instance
event_publisher = DaprEventPublisher()
