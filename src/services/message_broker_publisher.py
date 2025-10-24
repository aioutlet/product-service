"""
Message Broker Publisher Service
Publishes events to message broker service via HTTP
"""
import os
import httpx
from typing import Dict, Any
from src.observability import logger

class MessageBrokerPublisher:
    """Publisher for sending events to message broker service"""
    
    def __init__(self):
        self.broker_url = os.getenv('MESSAGE_BROKER_SERVICE_URL', 'http://localhost:4000')
        self.api_key = os.getenv('MESSAGE_BROKER_API_KEY', '')
        self.service_name = os.getenv('SERVICE_NAME', 'product-service')
        
    async def publish(self, event_type: str, data: Dict[str, Any], correlation_id: str = None):
        """
        Publish an event to the message broker service
        
        Args:
            event_type: The type of event (e.g., 'product.created')
            data: The event payload
            correlation_id: Optional correlation ID for tracing
        """
        try:
            payload = {
                'eventType': event_type,
                'source': self.service_name,
                'data': data,
                'correlationId': correlation_id
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id or ''
            }
            
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.broker_url}/api/publish",
                    json=payload,
                    headers=headers,
                    timeout=5.0
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"Published event: {event_type}", metadata={
                        "correlationId": correlation_id,
                        "eventType": event_type,
                        "source": self.service_name
                    })
                else:
                    logger.error(f"Failed to publish event: {event_type}", metadata={
                        "correlationId": correlation_id,
                        "eventType": event_type,
                        "statusCode": response.status_code,
                        "response": response.text
                    })
                    
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}", metadata={
                "correlationId": correlation_id,
                "eventType": event_type,
                "error": str(e)
            })
            # Don't raise - publishing failures shouldn't break main flow

# Singleton instance
_publisher = None

def get_publisher() -> MessageBrokerPublisher:
    """Get singleton publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = MessageBrokerPublisher()
    return _publisher
