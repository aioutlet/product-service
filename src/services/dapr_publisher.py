"""
Dapr Event Publisher Service
Publishes events via Dapr Pub/Sub using CloudEvents specification
"""
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, UTC
from src.core.logger import logger


class DaprPublisher:
    """Publisher for sending events via Dapr Pub/Sub"""
    
    def __init__(self):
        # Dapr sidecar configuration
        self.dapr_http_port = os.getenv('DAPR_HTTP_PORT', '3500')
        self.dapr_pubsub_name = os.getenv('DAPR_PUBSUB_NAME', 'product-pubsub')
        self.dapr_url = f"http://localhost:{self.dapr_http_port}"
        
        # Service metadata
        self.service_name = os.getenv('SERVICE_NAME', 'product-service')
        self.service_version = os.getenv('SERVICE_VERSION', '1.0.0')
        
    async def publish(
        self, 
        topic: str, 
        data: Dict[str, Any], 
        event_type: str,
        correlation_id: Optional[str] = None,
        data_content_type: str = "application/json"
    ) -> bool:
        """
        Publish an event to Dapr Pub/Sub using CloudEvents specification
        
        Args:
            topic: The topic to publish to (e.g., 'product.created')
            data: The event payload (the 'data' field in CloudEvents)
            event_type: The CloudEvents type (e.g., 'com.aioutlet.product.created.v1')
            correlation_id: Optional correlation ID for distributed tracing
            data_content_type: Content type of the data payload
            
        Returns:
            bool: True if published successfully, False otherwise
            
        CloudEvents Schema:
        {
            "specversion": "1.0",
            "type": "com.aioutlet.product.created.v1",
            "source": "product-service",
            "id": "unique-event-id",
            "time": "2025-11-04T10:00:00Z",
            "datacontenttype": "application/json",
            "data": { ... },
            "correlationid": "optional-correlation-id"
        }
        """
        try:
            # Generate unique event ID
            event_id = f"{self.service_name}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
            
            # Construct CloudEvents payload
            cloud_event = {
                "specversion": "1.0",
                "type": event_type,
                "source": self.service_name,
                "id": event_id,
                "time": datetime.now(UTC).isoformat(),
                "datacontenttype": data_content_type,
                "data": data
            }
            
            # Add optional correlation ID
            if correlation_id:
                cloud_event["correlationid"] = correlation_id
            
            # Dapr publish endpoint: POST /v1.0/publish/{pubsubname}/{topic}
            publish_url = f"{self.dapr_url}/v1.0/publish/{self.dapr_pubsub_name}/{topic}"
            
            headers = {
                "Content-Type": "application/cloudevents+json",
            }
            
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id
            
            # Publish to Dapr
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    publish_url,
                    json=cloud_event,
                    headers=headers
                )
                
                if response.status_code == 204 or response.status_code == 200:
                    logger.info(
                        f"Published event to Dapr: {event_type}",
                        metadata={
                            "correlationId": correlation_id,
                            "eventId": event_id,
                            "eventType": event_type,
                            "topic": topic,
                            "source": self.service_name,
                            "daprPubSubName": self.dapr_pubsub_name
                        }
                    )
                    return True
                else:
                    logger.error(
                        f"Failed to publish event to Dapr: {event_type}",
                        metadata={
                            "correlationId": correlation_id,
                            "eventId": event_id,
                            "eventType": event_type,
                            "topic": topic,
                            "statusCode": response.status_code,
                            "response": response.text,
                            "daprUrl": publish_url
                        }
                    )
                    return False
                    
        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout publishing event to Dapr: {event_type}",
                metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type,
                    "topic": topic,
                    "error": "Request timeout",
                    "daprUrl": self.dapr_url
                }
            )
            return False
            
        except httpx.ConnectError as e:
            logger.error(
                f"Cannot connect to Dapr sidecar: {str(e)}",
                metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type,
                    "topic": topic,
                    "error": "Connection refused",
                    "daprUrl": self.dapr_url,
                    "hint": "Ensure Dapr sidecar is running on port " + self.dapr_http_port
                }
            )
            return False
            
        except Exception as e:
            logger.error(
                f"Error publishing event to Dapr: {str(e)}",
                metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type,
                    "topic": topic,
                    "error": str(e),
                    "errorType": type(e).__name__
                }
            )
            return False


# Singleton instance
_publisher: Optional[DaprPublisher] = None


def get_dapr_publisher() -> DaprPublisher:
    """Get singleton Dapr publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = DaprPublisher()
    return _publisher
