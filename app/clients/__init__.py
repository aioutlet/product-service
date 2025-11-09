"""
Clients Package
External service clients for inter-service communication.
"""

from .inventory_client import (
    InventoryServiceClient,
    get_inventory_client,
    StockCheckItem,
    StockCheckResponse,
    InventoryItem
)
from .dapr_service_client import DaprServiceClient, get_dapr_service_client
from .dapr_secret_client import DaprSecretManager, secret_manager, get_database_config, get_jwt_config

__all__ = [
    "InventoryServiceClient",
    "get_inventory_client",
    "StockCheckItem",
    "StockCheckResponse",
    "InventoryItem",
    "DaprServiceClient",
    "get_dapr_service_client",
    "DaprSecretManager",
    "secret_manager",
    "get_database_config",
    "get_jwt_config"
]
