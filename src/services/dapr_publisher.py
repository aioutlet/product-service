"""
Dapr Event Publisher Service
Publishes events via Dapr Pub/Sub using CloudEvents specification
"""
import os
import httpx
from typing import Dict, Any, Optional, List
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
    
    # ===== Product-Specific Event Methods =====
    
    async def publish_product_created(
        self,
        product: Dict[str, Any],
        acting_user: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.created event
        
        Args:
            product: The created product data (full product document)
            acting_user: User ID who created the product
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "product": product,
            "actingUser": acting_user,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "created"
        }
        
        return await self.publish(
            topic="product.created",
            data=event_data,
            event_type="com.aioutlet.product.created.v1",
            correlation_id=correlation_id
        )
    
    async def publish_product_updated(
        self,
        product: Dict[str, Any],
        changes: Dict[str, Any],
        acting_user: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.updated event
        
        Args:
            product: The updated product data (full product document after update)
            changes: Dictionary of changed fields (e.g., {"price": {"old": 99.99, "new": 89.99}})
            acting_user: User ID who updated the product
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "product": product,
            "changes": changes,
            "actingUser": acting_user,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "updated"
        }
        
        return await self.publish(
            topic="product.updated",
            data=event_data,
            event_type="com.aioutlet.product.updated.v1",
            correlation_id=correlation_id
        )
    
    async def publish_product_deleted(
        self,
        product_id: str,
        sku: str,
        acting_user: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.deleted event
        
        Args:
            product_id: The MongoDB ObjectId of the deleted product
            sku: The SKU of the deleted product
            acting_user: User ID who deleted the product
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "productId": product_id,
            "sku": sku,
            "actingUser": acting_user,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "deleted"
        }
        
        return await self.publish(
            topic="product.deleted",
            data=event_data,
            event_type="com.aioutlet.product.deleted.v1",
            correlation_id=correlation_id
        )
    
    # ==================== Badge Events ====================
    
    async def publish_badge_assigned(
        self,
        product_id: str,
        badge_type: str,
        expires_at: Optional[str] = None,
        assigned_by: Optional[str] = None,
        automated: bool = False,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.badge.assigned event
        
        Args:
            product_id: The product ID that received the badge
            badge_type: Type of badge (e.g., 'new_arrival', 'best_seller', 'sale')
            expires_at: Optional expiration timestamp
            assigned_by: User ID who assigned the badge (or 'auto' if automated)
            automated: Whether the badge was assigned automatically
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "productId": product_id,
            "badgeType": badge_type,
            "expiresAt": expires_at,
            "assignedBy": assigned_by or ("auto" if automated else None),
            "automated": automated,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "badge_assigned"
        }
        
        return await self.publish(
            topic="product.badge.assigned",
            data=event_data,
            event_type="com.aioutlet.product.badge.assigned.v1",
            correlation_id=correlation_id
        )
    
    async def publish_badge_removed(
        self,
        product_id: str,
        badge_type: str,
        removed_by: Optional[str] = None,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.badge.removed event
        
        Args:
            product_id: The product ID from which badge was removed
            badge_type: Type of badge removed
            removed_by: User ID who removed the badge
            reason: Optional reason for removal (e.g., 'expired', 'manual', 'criteria_not_met')
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "productId": product_id,
            "badgeType": badge_type,
            "removedBy": removed_by,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "badge_removed"
        }
        
        return await self.publish(
            topic="product.badge.removed",
            data=event_data,
            event_type="com.aioutlet.product.badge.removed.v1",
            correlation_id=correlation_id
        )
    
    # ==================== Variation Events ====================
    
    async def publish_variation_created(
        self,
        parent_id: str,
        variation_id: str,
        variation_type: str,
        variant_attributes: Dict[str, Any],
        created_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.variation.created event
        
        Args:
            parent_id: The parent product ID
            variation_id: The created variation product ID
            variation_type: Type of variation (e.g., 'color', 'size', 'style')
            variant_attributes: Attributes that make this variation unique
            created_by: User ID who created the variation
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "parentId": parent_id,
            "variationId": variation_id,
            "variationType": variation_type,
            "variantAttributes": variant_attributes,
            "createdBy": created_by,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "variation_created"
        }
        
        return await self.publish(
            topic="product.variation.created",
            data=event_data,
            event_type="com.aioutlet.product.variation.created.v1",
            correlation_id=correlation_id
        )
    
    async def publish_variation_updated(
        self,
        parent_id: str,
        variation_id: str,
        changes: Dict[str, Any],
        updated_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.variation.updated event
        
        Args:
            parent_id: The parent product ID
            variation_id: The updated variation product ID
            changes: Dictionary of changed fields
            updated_by: User ID who updated the variation
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "parentId": parent_id,
            "variationId": variation_id,
            "changes": changes,
            "updatedBy": updated_by,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "variation_updated"
        }
        
        return await self.publish(
            topic="product.variation.updated",
            data=event_data,
            event_type="com.aioutlet.product.variation.updated.v1",
            correlation_id=correlation_id
        )
    
    async def publish_variation_deleted(
        self,
        parent_id: str,
        variation_id: str,
        deleted_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.variation.deleted event
        
        Args:
            parent_id: The parent product ID
            variation_id: The deleted variation product ID
            deleted_by: User ID who deleted the variation
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "parentId": parent_id,
            "variationId": variation_id,
            "deletedBy": deleted_by,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "variation_deleted"
        }
        
        return await self.publish(
            topic="product.variation.deleted",
            data=event_data,
            event_type="com.aioutlet.product.variation.deleted.v1",
            correlation_id=correlation_id
        )
    
    # ==================== Size Chart Events ====================
    
    async def publish_sizechart_assigned(
        self,
        size_chart_id: str,
        product_ids: List[str],
        assigned_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.sizechart.assigned event
        
        Args:
            size_chart_id: The size chart ID that was assigned
            product_ids: List of product IDs that received the size chart
            assigned_by: User ID who assigned the size chart
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "sizeChartId": size_chart_id,
            "productIds": product_ids,
            "productCount": len(product_ids),
            "assignedBy": assigned_by,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "sizechart_assigned"
        }
        
        return await self.publish(
            topic="product.sizechart.assigned",
            data=event_data,
            event_type="com.aioutlet.product.sizechart.assigned.v1",
            correlation_id=correlation_id
        )
    
    async def publish_sizechart_unassigned(
        self,
        size_chart_id: str,
        product_ids: List[str],
        unassigned_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.sizechart.unassigned event
        
        Args:
            size_chart_id: The size chart ID that was unassigned
            product_ids: List of product IDs from which size chart was removed
            unassigned_by: User ID who unassigned the size chart
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "sizeChartId": size_chart_id,
            "productIds": product_ids,
            "productCount": len(product_ids),
            "unassignedBy": unassigned_by,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "sizechart_unassigned"
        }
        
        return await self.publish(
            topic="product.sizechart.unassigned",
            data=event_data,
            event_type="com.aioutlet.product.sizechart.unassigned.v1",
            correlation_id=correlation_id
        )
    
    # ==================== Bulk Operation Events ====================
    
    async def publish_bulk_operation_completed(
        self,
        operation: str,
        success_count: int,
        failure_count: int,
        total_count: int,
        operation_id: Optional[str] = None,
        executed_by: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.bulk.completed event
        
        Args:
            operation: Type of operation (e.g., 'create', 'update', 'delete')
            success_count: Number of successful operations
            failure_count: Number of failed operations
            total_count: Total number of operations attempted
            operation_id: Optional unique operation identifier
            executed_by: User ID who executed the bulk operation
            details: Optional additional details about the operation
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "operation": operation,
            "successCount": success_count,
            "failureCount": failure_count,
            "totalCount": total_count,
            "operationId": operation_id,
            "executedBy": executed_by,
            "details": details or {},
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "bulk_completed"
        }
        
        return await self.publish(
            topic="product.bulk.completed",
            data=event_data,
            event_type="com.aioutlet.product.bulk.completed.v1",
            correlation_id=correlation_id
        )
    
    async def publish_bulk_operation_failed(
        self,
        operation: str,
        error_message: str,
        operation_id: Optional[str] = None,
        executed_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish product.bulk.failed event
        
        Args:
            operation: Type of operation that failed
            error_message: Error message describing the failure
            operation_id: Optional unique operation identifier
            executed_by: User ID who attempted the bulk operation
            correlation_id: Optional correlation ID for distributed tracing
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        event_data = {
            "operation": operation,
            "errorMessage": error_message,
            "operationId": operation_id,
            "executedBy": executed_by,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "bulk_failed"
        }
        
        return await self.publish(
            topic="product.bulk.failed",
            data=event_data,
            event_type="com.aioutlet.product.bulk.failed.v1",
            correlation_id=correlation_id
        )


# Singleton instance
_publisher: Optional[DaprPublisher] = None


def get_dapr_publisher() -> DaprPublisher:
    """Get singleton Dapr publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = DaprPublisher()
    return _publisher
