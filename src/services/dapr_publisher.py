"""
Dapr Publisher Service
Publishes events via Dapr pub/sub.
Implements PRD REQ-3.x: Event Publishing requirements.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dapr.clients import DaprClient

from src.observability.logging import logger


class DaprPublisher:
    """
    Publisher for sending events via Dapr pub/sub.
    Implements PRD REQ-3.x: Event Publishing requirements.
    """

    def __init__(self):
        self.dapr_http_port = os.getenv('DAPR_HTTP_PORT', '3500')
        self.dapr_grpc_port = os.getenv('DAPR_GRPC_PORT', '50001')
        self.pubsub_name = 'aioutlet-pubsub'
        self.service_name = os.getenv('SERVICE_NAME', 'product-service')

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Publish an event via Dapr pub/sub.

        Meets Requirements:
        - PRD REQ-3.1 to REQ-3.4: Specific event publishing
        - PRD REQ-3.5: Fire-and-forget, don't fail on publish error
        - PRD NFR-2.3: Automatic retries via Dapr
        - PRD NFR-5.1: Correlation ID propagation

        Args:
            event_type: Event type (e.g., 'product.created')
            data: Event payload
            correlation_id: Correlation ID for tracing
        """
        try:
            # Build event payload matching PRD event schema
            event_payload = {
                'eventType': event_type,
                'eventId': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': self.service_name,
                'correlationId': correlation_id,
                'data': data
            }

            # Publish via Dapr (using HTTP endpoint)
            # Dapr handles retries, durability, and routing
            with DaprClient(f'http://localhost:{self.dapr_http_port}') as client:
                client.publish_event(
                    pubsub_name=self.pubsub_name,
                    topic_name=event_type,  # Topic = event type
                    data=json.dumps(event_payload),
                    data_content_type='application/json'
                )

            logger.info(
                f"Published event via Dapr: {event_type}",
                metadata={
                    'correlationId': correlation_id,
                    'eventType': event_type,
                    'source': self.service_name,
                    'transport': 'dapr'
                }
            )

        except Exception as e:
            # Per PRD REQ-3.5: Log but don't fail the operation
            logger.error(
                f"Failed to publish event via Dapr: {str(e)}",
                metadata={
                    'correlationId': correlation_id,
                    'eventType': event_type,
                    'error': str(e),
                    'errorType': type(e).__name__
                }
            )
            # Don't raise - publishing failures shouldn't break main flow


# Singleton instance
_dapr_publisher = None


def get_dapr_publisher() -> DaprPublisher:
    """Get singleton Dapr publisher instance"""
    global _dapr_publisher
    if _dapr_publisher is None:
        _dapr_publisher = DaprPublisher()
    return _dapr_publisher
