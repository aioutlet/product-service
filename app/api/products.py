"""
Product API endpoints following FastAPI best practices
Clean API layer with dependency injection
"""

from typing import List

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.product import get_product_service
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.product import ProductService
from app.schemas.product import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse, 
    ProductSearchResponse,
    ProductStatsResponse
)
from app.core.errors import ErrorResponseModel

router = APIRouter()


# Internal endpoints (for inter-service communication)
@router.get(
    "/internal/{product_id}/exists",
    response_model=dict,
    tags=["internal"]
)
async def check_product_exists(
    product_id: str,
    service: ProductService = Depends(get_product_service),
):
    """
    Check if a product exists (internal endpoint for other services).
    
    Returns:
    - exists: Boolean indicating if the product exists and is active
    """
    return await service.check_product_exists(product_id)


# Product discovery endpoints
@router.get(
    "/trending-categories",
    response_model=list[dict],
    responses={503: {"model": ErrorResponseModel}},
)
async def get_trending_categories(
    limit: int = Query(5, ge=1, le=20, description="Max trending categories to return"),
    service: ProductService = Depends(get_product_service),
):
    """
    Get trending categories based on product popularity.
    
    Trending algorithm per category:
    - Product count in category
    - Average rating across products
    - Total reviews across products
    - Score = (avg_rating × total_reviews × product_count)
    - Returns top N categories by score
    """
    return await service.get_trending_categories(limit)


@router.get(
    "/trending",
    response_model=list[ProductResponse],
    responses={503: {"model": ErrorResponseModel}},
)
async def get_trending_products(
    limit: int = Query(4, ge=1, le=20, description="Max trending products to return"),
    service: ProductService = Depends(get_product_service),
):
    """
    Get recently created products (trending placeholder).
    
    NOTE: Full trending algorithm with reviews/ratings should be implemented in Web BFF
    by aggregating data from both Product Service and Review Service.
    
    This returns recently created products only.
    """
    return await service.get_trending_products(limit)


# Product search and listing
@router.get(
    "/search",
    response_model=ProductSearchResponse,
    responses={400: {"model": ErrorResponseModel}, 404: {"model": ErrorResponseModel}},
)
async def search_products(
    response: Response,
    q: str = Query(
        ...,
        description="Search text to find in product name or description",
        min_length=1,
    ),
    department: str = Query(None, description="Filter by department (e.g., Women, Men, Electronics)"),
    category: str = Query(None, description="Filter by category (e.g., Clothing, Accessories)"),
    subcategory: str = Query(None, description="Filter by subcategory (e.g., Tops, Laptops)"),
    min_price: float = Query(None, ge=0, description="Minimum price"),
    max_price: float = Query(None, ge=0, description="Maximum price"),
    tags: list[str] = Query(None, description="Filter by tags"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    service: ProductService = Depends(get_product_service),
):
    """
    Search products by text in name and description with optional filters.
    Supports hierarchical filtering by department/category/subcategory.
    Returns paginated results with metadata.
    """
    # Add no-cache headers to prevent client-side caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return await service.search_products(
        q, department, category, subcategory, min_price, max_price, tags, skip, limit
    )


@router.get(
    "/",
    response_model=ProductSearchResponse,
    responses={404: {"model": ErrorResponseModel}},
)
async def list_products(
    department: str = Query(None, description="Filter by department (e.g., Women, Men, Electronics)"),
    category: str = Query(None, description="Filter by category (e.g., Clothing, Accessories)"),
    subcategory: str = Query(None, description="Filter by subcategory (e.g., Tops, Laptops)"),
    min_price: float = Query(None, ge=0, description="Minimum price"),
    max_price: float = Query(None, ge=0, description="Maximum price"),
    tags: List[str] = Query(None, description="Filter by tags"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    service: ProductService = Depends(get_product_service),
):
    """
    List products with optional filters and pagination.
    Supports hierarchical filtering by department/category/subcategory.
    """
    return await service.list_products(
        department, category, subcategory, min_price, max_price, tags, skip, limit
    )


# CRUD operations
@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    responses={404: {"model": ErrorResponseModel}},
)
async def get_product(
    product_id: str, 
    service: ProductService = Depends(get_product_service)
):
    """
    Get a product by its ID.
    """
    return await service.get_product(product_id)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponseModel}, 401: {"model": ErrorResponseModel}},
)
async def create_product(
    product: ProductCreate, 
    service: ProductService = Depends(get_product_service),
    user: User = Depends(get_current_user)
):
    """
    Create a new product. Prevents duplicate SKUs and negative values.
    Requires authentication.
    """
    return await service.create_product(product, created_by=user.id)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        400: {"model": ErrorResponseModel},
        401: {"model": ErrorResponseModel},
        403: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel},
    },
)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    user: User = Depends(get_current_user)
):
    """
    Update a product. Only the creator or admin can update.
    Prevents duplicate SKUs and negative values.
    Requires authentication.
    """
    return await service.update_product(product_id, product, updated_by=user.id)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponseModel},
        403: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel}
    },
)
async def delete_product(
    product_id: str,
    service: ProductService = Depends(get_product_service),
    user: User = Depends(get_current_user)
):
    """
    Soft delete a product. Only the creator or admin can delete.
    Requires authentication.
    """
    await service.delete_product(product_id, deleted_by=user.email)


@router.patch(
    "/{product_id}/reactivate",
    response_model=ProductResponse,
    responses={
        401: {"model": ErrorResponseModel},
        403: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel}
    },
)
async def reactivate_product(
    product_id: str,
    service: ProductService = Depends(get_product_service),
    user: User = Depends(get_current_user)
):
    """
    Reactivate a soft-deleted product. Only admin can reactivate products.
    Requires admin authentication.
    """
    # Check if user is admin
    if not user.is_admin():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reactivate products"
        )
    
    return await service.reactivate_product(product_id, updated_by=user.id)