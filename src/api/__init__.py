"""
FastAPI route handlers (API layer).

This module contains all API route handlers organized by resource.
Uses dependency injection for services, authentication, and database access.
"""

# Route handlers organized by resource
from .products import router as products_router
from .variations import router as variations_router
from .badges import router as badges_router
from .health import router as health_router
from .admin import router as admin_router
from .restrictions import router as restrictions_router

__all__ = [
    "products_router",
    "variations_router",
    "badges_router",
    "health_router",
    "admin_router",
    "restrictions_router",
]
