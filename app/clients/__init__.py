"""
Clients Package
External service clients for inter-service communication.
"""

from .inventory import (
    InventoryServiceClient,
    get_inventory_client,
    StockCheckItem,
    StockCheckResponse,
    InventoryItem
)

__all__ = [
    "InventoryServiceClient",
    "get_inventory_client",
    "StockCheckItem",
    "StockCheckResponse",
    "InventoryItem"
]
