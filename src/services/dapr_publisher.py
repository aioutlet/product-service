"""Simple Dapr Publisher Service"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class DaprPublisher:
    """Simple Dapr publisher for product events"""
    
    def __init__(self):
        self.dapr_port = os.getenv('DAPR_HTTP_PORT', '3500')
        self.pubsub_name = os.getenv('DAPR_PUBSUB_NAME', 'product-pubsub')
        self.app_id = os.getenv('DAPR_APP_ID', 'product-service')
        self.base_url = f"http://localhost:{self.dapr_port}"
        
    async def publish_event(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        product_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Publish an event to Dapr pub/sub"""
        try:
            event = {
                "specversion": "1.0",
                "type": event_type,
                "source": f"/{self.app_id}",
                "id": f"{event_type}-{datetime.utcnow().isoformat()}",
                "time": datetime.utcnow().isoformat() + "Z",
                "datacontenttype": "application/json",
                "data": data
            }
            
            if product_id:
                event["subject"] = f"product/{product_id}"
            if correlation_id:
                event["correlationid"] = correlation_id
                
            url = f"{self.base_url}/v1.0/publish/{self.pubsub_name}/{topic}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=event,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=5.0)
                ) as response:
                    if response.status == 204:
                        logger.info(f"Event published successfully: {event_type}")
                        return True
                    else:
                        logger.error(f"Failed to publish event: {event_type}")
                        return False
        except Exception as e:
            logger.error(f"Error publishing event: {event_type} - {e}")
            return False
    
    async def publish_product_created(self, product_data: Dict[str, Any], correlation_id: Optional[str] = None) -> bool:
        """Publish product.created event"""
        return await self.publish_event(
            topic="product.events",
            event_type="product.created",
            data=product_data,
            product_id=str(product_data.get("_id", "")),
            correlation_id=correlation_id
        )
    
    async def publish_product_updated(self, product_data: Dict[str, Any], changes: Dict[str, Any], correlation_id: Optional[str] = None) -> bool:
        """Publish product.updated event"""
        event_data = {"product": product_data, "changes": changes}
        return await self.publish_event(
            topic="product.events",
            event_type="product.updated",
            data=event_data,
            product_id=str(product_data.get("_id", "")),
            correlation_id=correlation_id
        )
    
    async def publish_product_deleted(self, product_id: str, correlation_id: Optional[str] = None) -> bool:
        """Publish product.deleted event"""
        event_data = {
            "product_id": product_id,
            "deleted_at": datetime.utcnow().isoformat() + "Z"
        }
        return await self.publish_event(
            topic="product.events",
            event_type="product.deleted",
            data=event_data,
            product_id=product_id,
            correlation_id=correlation_id
        )

    async def health_check(self) -> bool:
        """Check if Dapr sidecar is healthy"""
        try:
            url = f"{self.base_url}/v1.0/healthz"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    return response.status == 200
        except Exception:
            return False


_publisher: Optional[DaprPublisher] = None


def get_dapr_publisher() -> DaprPublisher:
    """Get the global Dapr publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = DaprPublisher()
    return _publisher
