"""
Inventory Service Client (Dapr Service Invocation)

This module provides a client to interact with the inventory-service
using Dapr service invocation. Dapr handles service discovery, retries,
circuit breaking, and distributed tracing automatically.
"""

from typing import List, Optional

from pydantic import BaseModel

from src.core.logger import logger
from .dapr_service_client import get_dapr_client


class StockCheckItem(BaseModel):
    sku: str
    quantity: int


class StockCheckItemResult(BaseModel):
    sku: str
    requested_quantity: int
    available_quantity: int
    available: bool


class StockCheckResponse(BaseModel):
    available: bool
    items: List[StockCheckItemResult]


class InventoryItem(BaseModel):
    sku: str
    quantity_available: int
    quantity_reserved: int
    reorder_level: int
    max_stock: int
    warehouse_location: Optional[str] = None
    supplier: Optional[str] = None


class InventoryServiceClient:
    """
    Client for communicating with the inventory-service via Dapr service invocation.

    This client provides methods to check stock availability,
    get inventory information, and other inventory-related operations.
    
    Benefits of using Dapr service invocation:
    - No need to know inventory service URL
    - Automatic service discovery
    - Built-in retries and circuit breaking
    - Distributed tracing propagation
    - mTLS for secure communication
    """

    def __init__(self, app_id: str = "inventory-service"):
        """
        Initialize the inventory service client with Dapr.

        Args:
            app_id: Dapr app ID of the inventory service (default: inventory-service)
        """
        self.app_id = app_id
        self.dapr_client = get_dapr_client()

    async def check_stock(self, items: List[StockCheckItem]) -> StockCheckResponse:
        """
        Check stock availability for multiple items via Dapr.

        Args:
            items: List of items to check stock for

        Returns:
            StockCheckResponse: Stock availability information

        Raises:
            Exception: If the Dapr invocation fails
        """
        try:
            data = await self.dapr_client.invoke_post(
                app_id=self.app_id,
                method="stock/check",
                data={"items": [item.model_dump() for item in items]}
            )
            return StockCheckResponse(**data)
        except Exception as e:
            logger.error(
                f"Failed to check stock with inventory service via Dapr: {e}",
                metadata={"appId": self.app_id, "error": str(e)}
            )
            raise

    async def get_inventory_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """
        Get inventory information for a specific SKU via Dapr.

        Args:
            sku: Product SKU

        Returns:
            InventoryItem: Inventory information or None if not found

        Raises:
            Exception: If the Dapr invocation fails
        """
        try:
            data = await self.dapr_client.invoke_get(
                app_id=self.app_id,
                method=f"inventory/sku/{sku}"
            )
            if data is None:
                return None
            return InventoryItem(**data)
        except Exception as e:
            logger.error(
                f"Failed to get inventory for SKU {sku} via Dapr: {e}",
                metadata={"appId": self.app_id, "sku": sku, "error": str(e)}
            )
            raise

    async def get_inventory_by_product_id(
        self, product_id: str
    ) -> Optional[InventoryItem]:
        """
        Get inventory information for a specific product ID via Dapr.

        Args:
            product_id: Product ID (MongoDB ObjectId)

        Returns:
            InventoryItem: Inventory information or None if not found

        Raises:
            Exception: If the Dapr invocation fails
        """
        try:
            data = await self.dapr_client.invoke_get(
                app_id=self.app_id,
                method=f"inventory/product/{product_id}"
            )
            if data is None:
                return None
            return InventoryItem(**data)
        except Exception as e:
            logger.error(
                f"Failed to get inventory for product {product_id} via Dapr: {e}",
                metadata={"appId": self.app_id, "productId": product_id, "error": str(e)}
            )
            raise

    async def get_multiple_inventory(self, skus: List[str]) -> List[InventoryItem]:
        """
        Get inventory information for multiple SKUs via Dapr.

        Args:
            skus: List of product SKUs

        Returns:
            List[InventoryItem]: List of inventory items

        Raises:
            Exception: If the Dapr invocation fails
        """
        try:
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

            return inventory_items
        except Exception as e:
            logger.error(
                f"Failed to get multiple inventory items via Dapr: {e}",
                metadata={"appId": self.app_id, "skuCount": len(skus), "error": str(e)}
            )
            raise

    async def is_sku_available(self, sku: str, quantity: int = 1) -> bool:
        """
        Check if a specific quantity is available for a SKU via Dapr.

        Args:
            sku: Product SKU
            quantity: Quantity to check (default: 1)

        Returns:
            bool: True if quantity is available, False otherwise
        """
        try:
            response = await self.check_stock(
                [StockCheckItem(sku=sku, quantity=quantity)]
            )
            has_response = response.available
            has_items = len(response.items) > 0
            item_available = response.items[0].available if has_items else False
            return has_response and has_items and item_available
        except Exception:
            logger.warning(
                f"Could not check availability for SKU {sku} via Dapr",
                metadata={"appId": self.app_id, "sku": sku}
            )
            return False

    async def close(self):
        """Close the Dapr service client."""
        # Dapr client cleanup is handled by the singleton get_dapr_client()
        pass


# Global client instance
_inventory_client: Optional[InventoryServiceClient] = None


def get_inventory_client() -> InventoryServiceClient:
    """
    Get the global inventory service client instance.

    Returns:
        InventoryServiceClient: The client instance
    """
    global _inventory_client
    if _inventory_client is None:
        # TODO: Load base_url from configuration
        _inventory_client = InventoryServiceClient()
    return _inventory_client


async def close_inventory_client():
    """Close the global inventory client."""
    global _inventory_client
    if _inventory_client:
        await _inventory_client.close()
        _inventory_client = None
