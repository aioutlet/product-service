"""
Admin API endpoints
Administrative operations and dashboard statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import logger
from app.dependencies.product import get_product_service
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.product import ProductStatsResponse
from app.services.product import ProductService

router = APIRouter()


@router.get(
    "/products/stats",
    response_model=ProductStatsResponse,
    summary="Get Product Statistics",
    description="Get comprehensive product statistics for admin dashboard"
)
async def get_product_stats(
    service: ProductService = Depends(get_product_service),
    user: User = Depends(require_admin)  # Admin only
):
    """
    Get product statistics for admin dashboard.
    Requires admin role.
    
    Returns:
    - total: Total number of products
    - active: Number of active products
    - lowStock: Products with low stock (placeholder)
    - outOfStock: Out of stock products (placeholder)
    """
    logger.info(
        "Admin requesting product statistics",
        metadata={
            "event": "admin_stats_request",
            "user_id": user.id,
            "user_email": user.email
        }
    )
    
    stats = await service.get_admin_stats()
    
    logger.info(
        "Product statistics retrieved",
        metadata={
            "event": "admin_stats_retrieved",
            "total_products": stats.total,
            "active_products": stats.active
        }
    )
    
    return stats


@router.get(
    "/dashboard/summary",
    summary="Get Dashboard Summary",
    description="Get comprehensive dashboard summary for administrators"
)
async def get_dashboard_summary(
    service: ProductService = Depends(get_product_service),
    user: User = Depends(require_admin)  # Admin only
):
    """
    Get comprehensive dashboard summary.
    Requires admin role.
    
    Includes:
    - Product statistics
    - System health status
    - Recent activity
    """
    logger.info(
        "Admin requesting dashboard summary",
        metadata={
            "event": "admin_dashboard_request",
            "user_id": user.id,
            "user_email": user.email
        }
    )
    
    # Get product stats
    product_stats = await service.get_admin_stats()
    
    return {
        "products": product_stats.model_dump(),
        "user": {
            "id": user.id,
            "email": user.email,
            "roles": user.roles
        },
        "timestamp": logger._get_timestamp()
    }
