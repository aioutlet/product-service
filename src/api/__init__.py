"""
FastAPI route handlers (API layer).

This module contains all API route handlers organized by resource.
Uses dependency injection for services, authentication, and database access.
"""

# Route handlers organized by resource
from .products import router as products_router
from .health import router as health_router
from .admin import router as admin_router

__all__ = [
    "products_router",
    "health_router",
    "admin_router",
]
