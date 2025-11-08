"""
Dapr Event Consumer for Inventory Events
Handles inventory-related events from inventory service via Dapr pub/sub
"""

from typing import Dict, Any

from app.core.logger import logger
from app.repositories.product import ProductRepository


class InventoryEventConsumer:
    """
    Consumer for handling inventory-related events.
    Updates product availability and stock status based on inventory changes.
    """
    
    def __init__(self):
        self.db = None
        self.product_repo = None
    
    async def initialize(self):
        """Initialize database connection and repository"""
        if not self.db:
            # Lazy import to avoid circular dependency
            from app.db.mongodb import get_database
            self.db = await get_database()
            self.product_repo = ProductRepository(self.db)
    
    async def handle_inventory_updated(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle inventory.updated event.
        Updates product stock status when inventory changes.
        
        Args:
            event_data: CloudEvents formatted event data
            
        Returns:
            Response dict with status
        """
        try:
            await self.initialize()
            
            correlation_id = event_data.get("correlationId", "no-correlation")
            data = event_data.get("data", {})
            
            product_id = data.get("productId")
            stock_level = data.get("stockLevel")
            
            if not product_id or stock_level is None:
                logger.warning(
                    "Invalid inventory.updated event - missing required fields",
                    metadata={"correlationId": correlation_id}
                )
                return {"status": "error", "message": "Missing required fields"}
            
            logger.info(
                f"Processing inventory.updated event for product {product_id}",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "stockLevel": stock_level
                }
            )
            
            # TODO: Add logic to update product stock status
            # Example: Update is_available, stock_level, etc.
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(
                f"Error processing inventory.updated event: {str(e)}",
                metadata={
                    "correlationId": event_data.get("correlationId", "no-correlation"),
                    "error": str(e)
                }
            )
            return {"status": "error", "message": str(e)}
    
    async def handle_inventory_low_stock(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle inventory.low_stock event.
        Marks product when inventory is running low.
        
        Args:
            event_data: CloudEvents formatted event data
            
        Returns:
            Response dict with status
        """
        try:
            await self.initialize()
            
            correlation_id = event_data.get("correlationId", "no-correlation")
            data = event_data.get("data", {})
            
            product_id = data.get("productId")
            
            logger.info(
                f"Processing inventory.low_stock event for product {product_id}",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id
                }
            )
            
            # TODO: Add logic to handle low stock notification
            # Example: Set low_stock flag, trigger reorder notification
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(
                f"Error processing inventory.low_stock event: {str(e)}",
                metadata={
                    "correlationId": event_data.get("correlationId", "no-correlation"),
                    "error": str(e)
                }
            )
            return {"status": "error", "message": str(e)}


# Global consumer instance
inventory_event_consumer = InventoryEventConsumer()
