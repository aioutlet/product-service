# Router modules for the product service
from .bulk_router import router as bulk_router
from .home_router import router as home_router
from .import_export_router import router as import_export_router
from .product_router import router as product_router
from .review_router import router as review_router

__all__ = [
    "product_router",
    "review_router",
    "bulk_router",
    "import_export_router",
    "home_router",
]
