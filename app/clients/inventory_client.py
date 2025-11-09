"""
Inventory Service Client
Provides integration with inventory-service using Dapr service invocation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.logger import logger
from app.clients.dapr_service_client import get_dapr_service_client


class StockCheckItem(BaseModel):
    """Item to check stock for"""
    sku: str = Field(..., description="Product SKU")
    quantity: int = Field(..., gt=0, description="Quantity to check")


class StockCheckItemResult(BaseModel):
    """Result of stock check for a single item"""
    sku: str
    requested_quantity: int
    available_quantity: int
    available: bool


class StockCheckResponse(BaseModel):
    """Response from stock check endpoint"""
    available: bool = Field(..., description="Whether all requested items are available")
    items: List[StockCheckItemResult] = Field(..., description="Individual item results")


class InventoryItem(BaseModel):
    """Inventory item details"""
    sku: str
    quantity_available: int = Field(..., ge=0)
    quantity_reserved: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    max_stock: int = Field(..., ge=0)
    warehouse_location: Optional[str] = None
    supplier: Optional[str] = None


class InventoryServiceClient:
    """
    Client for communicating with inventory-service via Dapr service invocation.
    Provides methods for stock checking, inventory queries, and related operations.
    """

    def __init__(self):
        """Initialize the Dapr-based inventory service client"""
        self.dapr_client = get_dapr_service_client()
        self.app_id = "inventory-service"
        
        logger.info(
            "Inventory service client initialized",
            metadata={
                "event": "inventory_client_init",
                "target_service": self.app_id
            }
        )

    async def check_stock(self, items: List[StockCheckItem]) -> StockCheckResponse:
        """
        Check stock availability for multiple items.

        Args:
            items: List of items to check stock for

        Returns:
            StockCheckResponse with availability information

        Raises:
            Exception: If the request fails
        """
        try:
            logger.info(
                f"Checking stock for {len(items)} items",
                metadata={
                    "event": "inventory_check_stock",
                    "item_count": len(items),
                    "skus": [item.sku for item in items]
                }
            )
            
            response_data = await self.dapr_client.post(
                app_id=self.app_id,
                method_name="api/stock/check",
                data={"items": [item.model_dump() for item in items]}
            )
            
            result = StockCheckResponse(**response_data)
            
            logger.info(
                f"Stock check complete: {'available' if result.available else 'unavailable'}",
                metadata={
                    "event": "inventory_check_complete",
                    "available": result.available,
                    "items_checked": len(result.items)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to check stock: {str(e)}",
                metadata={
                    "event": "inventory_check_error",
                    "error": str(e),
                    "item_count": len(items)
                }
            )
            raise

    async def get_inventory_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """
        Get inventory information for a specific SKU.

        Args:
            sku: Product SKU

        Returns:
            InventoryItem if found, None otherwise

        Raises:
            Exception: If the request fails (except 404)
        """
        try:
            logger.debug(
                f"Getting inventory for SKU: {sku}",
                metadata={"event": "inventory_get_by_sku", "sku": sku}
            )
            
            response_data = await self.dapr_client.get(
                app_id=self.app_id,
                method_name=f"api/inventory/sku/{sku}"
            )
            
            return InventoryItem(**response_data)
            
        except Exception as e:
            if "404" in str(e):
                logger.debug(
                    f"Inventory not found for SKU: {sku}",
                    metadata={"event": "inventory_not_found", "sku": sku}
                )
                return None
            logger.error(
                f"Failed to get inventory for SKU {sku}: {str(e)}",
                metadata={"event": "inventory_get_error", "sku": sku, "error": str(e)}
            )
            raise

    async def get_inventory_by_product_id(self, product_id: str) -> Optional[InventoryItem]:
        """
        Get inventory information for a specific product ID.

        Args:
            product_id: Product ID (MongoDB ObjectId)

        Returns:
            InventoryItem if found, None otherwise

        Raises:
            Exception: If the request fails (except 404)
        """
        try:
            logger.debug(
                f"Getting inventory for product: {product_id}",
                metadata={"event": "inventory_get_by_product", "product_id": product_id}
            )
            
            response_data = await self.dapr_client.get(
                app_id=self.app_id,
                method_name=f"api/inventory/product/{product_id}"
            )
            
            return InventoryItem(**response_data)
            
        except Exception as e:
            if "404" in str(e):
                logger.debug(
                    f"Inventory not found for product: {product_id}",
                    metadata={"event": "inventory_not_found", "product_id": product_id}
                )
                return None
            logger.error(
                f"Failed to get inventory for product {product_id}: {str(e)}",
                metadata={"event": "inventory_get_error", "product_id": product_id, "error": str(e)}
            )
            raise

    async def get_multiple_inventory(self, skus: List[str]) -> List[InventoryItem]:
        """
        Get inventory information for multiple SKUs.

        Args:
            skus: List of product SKUs

        Returns:
            List of InventoryItem objects

        Raises:
            Exception: If the request fails
        """
        try:
            logger.info(
                f"Getting inventory for {len(skus)} SKUs",
                metadata={
                    "event": "inventory_get_multiple",
                    "sku_count": len(skus),
                    "skus": skus
                }
            )
            
            # Use the stock check endpoint which supports multiple SKUs
            check_items = [StockCheckItem(sku=sku, quantity=1) for sku in skus]
            stock_response = await self.check_stock(check_items)

            # Get detailed inventory for each available item
            inventory_items = []
            for item_result in stock_response.items:
                if item_result.available_quantity > 0:
                    inventory = await self.get_inventory_by_sku(item_result.sku)
                    if inventory:
                        inventory_items.append(inventory)

            logger.info(
                f"Retrieved {len(inventory_items)} inventory items",
                metadata={
                    "event": "inventory_get_multiple_complete",
                    "items_found": len(inventory_items)
                }
            )
            
            return inventory_items
            
        except Exception as e:
            logger.error(
                f"Failed to get multiple inventory items: {str(e)}",
                metadata={
                    "event": "inventory_get_multiple_error",
                    "error": str(e),
                    "sku_count": len(skus)
                }
            )
            raise

    async def is_sku_available(self, sku: str, quantity: int = 1) -> bool:
        """
        Check if a specific quantity is available for a SKU.

        Args:
            sku: Product SKU
            quantity: Quantity to check (default: 1)

        Returns:
            True if quantity is available, False otherwise
        """
        try:
            response = await self.check_stock(
                [StockCheckItem(sku=sku, quantity=quantity)]
            )
            
            has_response = response.available
            has_items = len(response.items) > 0
            item_available = response.items[0].available if has_items else False
            
            is_available = has_response and has_items and item_available
            
            logger.debug(
                f"SKU availability check: {sku} - {'available' if is_available else 'unavailable'}",
                metadata={
                    "event": "inventory_availability_check",
                    "sku": sku,
                    "quantity": quantity,
                    "available": is_available
                }
            )
            
            return is_available
            
        except Exception as e:
            logger.warning(
                f"Could not check availability for SKU {sku}: {str(e)}",
                metadata={
                    "event": "inventory_availability_error",
                    "sku": sku,
                    "error": str(e)
                }
            )
            return False

    async def health_check(self) -> bool:
        """
        Check if inventory service is reachable via Dapr.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            await self.dapr_client.get(
                app_id=self.app_id,
                method_name="health"
            )
            return True
        except Exception:
            return False


# Global client instance
_inventory_client: Optional[InventoryServiceClient] = None


def get_inventory_client() -> InventoryServiceClient:
    """
    Get the global inventory service client instance.
    Creates a new instance if one doesn't exist.

    Returns:
        InventoryServiceClient instance
    """
    global _inventory_client
    if _inventory_client is None:
        _inventory_client = InventoryServiceClient()
    return _inventory_client
