"""
Dependencies module initialization
"""

from .auth import get_current_user, require_admin
from .product import get_product_service

__all__ = [
    "get_current_user",
    "require_admin",
    "get_product_service",
]