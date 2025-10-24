"""
Inventory Service Client

This module provides a client to interact with the inventory-service
for stock-related operations. This follows the microservices pattern
where the product-service queries the inventory-service for stock information.
"""

from typing import List, Optional

import httpx
from pydantic import BaseModel

from src.core.logger import get_logger

logger = get_logger(__name__)


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
    Client for communicating with the inventory-service.

    This client provides methods to check stock availability,
    get inventory information, and other inventory-related operations.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the inventory service client.

        Args:
            base_url: Base URL of the inventory service
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient()

    async def check_stock(self, items: List[StockCheckItem]) -> StockCheckResponse:
        """
        Check stock availability for multiple items.

        Args:
            items: List of items to check stock for

        Returns:
            StockCheckResponse: Stock availability information

        Raises:
            httpx.HTTPError: If the request fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/stock/check",
                json={"items": [item.model_dump() for item in items]},
            )
            response.raise_for_status()
            data = response.json()
            return StockCheckResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"Failed to check stock with inventory service: {e}")
            raise

    async def get_inventory_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """
        Get inventory information for a specific SKU.

        Args:
            sku: Product SKU

        Returns:
            InventoryItem: Inventory information or None if not found

        Raises:
            httpx.HTTPError: If the request fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/inventory/sku/{sku}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return InventoryItem(**data)
        except httpx.HTTPError as e:
            logger.error(f"Failed to get inventory for SKU {sku}: {e}")
            raise

    async def get_inventory_by_product_id(
        self, product_id: str
    ) -> Optional[InventoryItem]:
        """
        Get inventory information for a specific product ID.

        Args:
            product_id: Product ID (MongoDB ObjectId)

        Returns:
            InventoryItem: Inventory information or None if not found

        Raises:
            httpx.HTTPError: If the request fails
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/inventory/product/{product_id}"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return InventoryItem(**data)
        except httpx.HTTPError as e:
            logger.error(f"Failed to get inventory for product {product_id}: {e}")
            raise

    async def get_multiple_inventory(self, skus: List[str]) -> List[InventoryItem]:
        """
        Get inventory information for multiple SKUs.

        Args:
            skus: List of product SKUs

        Returns:
            List[InventoryItem]: List of inventory items

        Raises:
            httpx.HTTPError: If the request fails
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
        except httpx.HTTPError as e:
            logger.error(f"Failed to get multiple inventory items: {e}")
            raise

    async def is_sku_available(self, sku: str, quantity: int = 1) -> bool:
        """
        Check if a specific quantity is available for a SKU.

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
        except httpx.HTTPError:
            logger.warning(f"Could not check availability for SKU {sku}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


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
