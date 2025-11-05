"""
Badge API endpoints.

This module defines REST API endpoints for badge management operations.
All write operations require admin authentication.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from src.models.badge import (
    BadgeType,
    AssignBadgeRequest,
    RemoveBadgeRequest,
    BulkAssignBadgeRequest,
    EvaluateBadgeRulesRequest,
    BadgeRuleEvaluationResponse,
    ProductBadgesResponse,
    BadgeStatistics
)
from src.services.badge_service import BadgeService
from src.dependencies.auth import get_current_user, require_admin
from src.dependencies.services import get_badge_service


router = APIRouter(prefix="/badges", tags=["badges"])


@router.post(
    "/assign",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    dependencies=[Depends(require_admin)],
    summary="Assign badge to product",
    description="Manually assign a badge to a product. Requires admin authentication."
)
async def assign_badge(
    request: AssignBadgeRequest,
    current_user: dict = Depends(get_current_user),
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Assign a badge to a product.
    
    - **productId**: ID of the product
    - **badgeType**: Type of badge (NEW, SALE, TRENDING, FEATURED, BEST_SELLER, LOW_STOCK)
    - **expiresAt**: Optional expiration date
    - **metadata**: Additional badge-specific data
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        product = await badge_service.assign_badge(
            product_id=request.productId,
            badge_type=request.badgeType,
            assigned_by=user_id,
            expires_at=request.expiresAt,
            metadata=request.metadata
        )
        return {
            "success": True,
            "message": f"Badge {request.badgeType.value} assigned to product {request.productId}",
            "data": product
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/remove",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    dependencies=[Depends(require_admin)],
    summary="Remove badge from product",
    description="Remove a badge from a product. Requires admin authentication."
)
async def remove_badge(
    request: RemoveBadgeRequest,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Remove a badge from a product.
    
    - **productId**: ID of the product
    - **badgeType**: Type of badge to remove
    """
    try:
        product = await badge_service.remove_badge(
            product_id=request.productId,
            badge_type=request.badgeType
        )
        return {
            "success": True,
            "message": f"Badge {request.badgeType.value} removed from product {request.productId}",
            "data": product
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/bulk-assign",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    dependencies=[Depends(require_admin)],
    summary="Bulk assign badge to products",
    description="Assign a badge to multiple products at once. Requires admin authentication."
)
async def bulk_assign_badge(
    request: BulkAssignBadgeRequest,
    current_user: dict = Depends(get_current_user),
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Assign a badge to multiple products.
    
    - **productIds**: List of product IDs
    - **badgeType**: Type of badge to assign
    - **expiresAt**: Optional expiration date
    - **metadata**: Additional badge-specific data
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        results = await badge_service.bulk_assign_badge(
            product_ids=request.productIds,
            badge_type=request.badgeType,
            assigned_by=user_id,
            expires_at=request.expiresAt,
            metadata=request.metadata
        )
        return {
            "success": True,
            "message": f"Bulk badge assignment completed",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/product/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductBadgesResponse,
    summary="Get product badges",
    description="Retrieve all badges for a product with display priority."
)
async def get_product_badges(
    product_id: str,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Get all badges for a product.
    
    Returns active badges with the highest priority badge for display.
    """
    try:
        badges = await badge_service.get_product_badges(product_id)
        return badges
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/evaluate-rules",
    status_code=status.HTTP_200_OK,
    response_model=BadgeRuleEvaluationResponse,
    dependencies=[Depends(require_admin)],
    summary="Evaluate badge rules",
    description="Evaluate automated badge rules for products. Requires admin authentication."
)
async def evaluate_badge_rules(
    request: EvaluateBadgeRulesRequest,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Evaluate automated badge assignment rules.
    
    - **productIds**: Optional list of product IDs (None = all active products)
    - **badgeTypes**: Optional list of badge types to evaluate (None = all types)
    - **dryRun**: If true, returns what would change without applying
    """
    try:
        results = await badge_service.evaluate_badge_rules(
            product_ids=request.productIds,
            badge_types=request.badgeTypes,
            dry_run=request.dryRun
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/expired",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    dependencies=[Depends(require_admin)],
    summary="Remove expired badges",
    description="Remove all expired badges from products. Requires admin authentication."
)
async def remove_expired_badges(
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Remove expired badges from all products.
    
    This endpoint should be called periodically (e.g., daily cron job).
    """
    try:
        results = await badge_service.remove_expired_badges()
        return {
            "success": True,
            "message": "Expired badges removed",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/statistics",
    status_code=status.HTTP_200_OK,
    response_model=BadgeStatistics,
    dependencies=[Depends(require_admin)],
    summary="Get badge statistics",
    description="Retrieve statistics about badge usage across the platform. Requires admin authentication."
)
async def get_badge_statistics(
    badge_service: BadgeService = Depends(get_badge_service)
):
    """
    Get badge statistics.
    
    Returns:
    - Total badge count
    - Badges by type
    - Products with badges
    - Automated vs manual badges
    - Expired badges
    """
    try:
        stats = await badge_service.get_badge_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
