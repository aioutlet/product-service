"""
FastAPI dependency injection functions.

This module contains dependency providers for database connections,
authentication, services, and other injectable components.
"""

from src.core.database import get_db, get_product_collection
from src.dependencies.auth import (
    get_current_user,
    get_optional_user,
    require_role,
    require_admin,
    CurrentUser
)
from src.dependencies.services import (
    get_product_repository,
    get_product_service,
    get_size_chart_repository,
    get_size_chart_service,
    get_size_charts_collection
)
from src.utils.correlation_id import get_correlation_id

# Alias for consistency with other services
get_database = get_db
get_products_collection = get_product_collection

__all__ = [
    "get_database",
    "get_db",
    "get_products_collection",
    "get_product_collection",
    "get_current_user",
    "get_optional_user",
    "require_role",
    "require_admin",
    "CurrentUser",
    "get_product_repository",
    "get_product_service",
    "get_size_chart_repository",
    "get_size_chart_service",
    "get_size_charts_collection",
    "get_correlation_id"
]
