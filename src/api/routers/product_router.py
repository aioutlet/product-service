from fastapi import APIRouter, Depends, Query, Response, status

import src.api.controllers.product_controller as product_controller
from src.shared.core.auth import get_current_user
from src.shared.core.errors import ErrorResponseModel
from src.shared.db.mongodb import get_product_collection
from src.shared.models.product import (
    ProductCreate,
    ProductDB,
    ProductSearchResponse,
    ProductUpdate,
)

from .bulk_router import router as bulk_router
from .import_export_router import router as import_export_router
from .review_router import router as review_router

# Main product router that combines all product-related routes
router = APIRouter()

# Include all sub-routers FIRST (before parameterized routes)
router.include_router(review_router, tags=["reviews"])
router.include_router(bulk_router, tags=["bulk-operations"])
router.include_router(import_export_router, tags=["import-export"])


# Product CRUD operations
@router.get(
    "/trending-categories",
    response_model=list[dict],
    responses={503: {"model": ErrorResponseModel}},
)
async def get_trending_categories(
    limit: int = Query(5, ge=1, le=20, description="Max trending categories to return"),
    collection=Depends(get_product_collection),
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
    return await product_controller.get_trending_categories(collection, limit)


@router.get(
    "/trending",
    response_model=list[ProductDB],
    responses={503: {"model": ErrorResponseModel}},
)
async def get_trending_products(
    limit: int = Query(4, ge=1, le=20, description="Max trending products to return"),
    collection=Depends(get_product_collection),
):
    """
    Get trending products based on ratings, reviews, and recency.
    
    Trending algorithm:
    - Considers products with at least 3 reviews
    - Scores based on: average_rating × num_reviews
    - Recent products (< 30 days old) get 1.5x boost
    - Returns top N products by score
    """
    return await product_controller.get_trending_products(collection, limit)


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
    collection=Depends(get_product_collection),
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

    return await product_controller.search_products(
        collection, q, department, category, subcategory, min_price, max_price, tags, skip, limit
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
    tags: list[str] = Query(None, description="Filter by tags"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    collection=Depends(get_product_collection),
):
    """
    List products with optional filters and pagination.
    Supports hierarchical filtering by department/category/subcategory.
    """
    return await product_controller.list_products(
        collection, department, category, subcategory, min_price, max_price, tags, skip, limit
    )


@router.get(
    "/{product_id}",
    response_model=ProductDB,
    responses={404: {"model": ErrorResponseModel}},
)
async def get_product(product_id: str, collection=Depends(get_product_collection)):
    """
    Get a product by its ID.
    """
    return await product_controller.get_product(product_id, collection)


@router.post(
    "/",
    response_model=ProductDB,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponseModel}},
)
async def create_product(
    product: ProductCreate, collection=Depends(get_product_collection)
):
    """
    Create a new product. Prevents duplicate SKUs and negative values.
    """
    return await product_controller.create_product(product, collection)


@router.patch(
    "/{product_id}",
    response_model=ProductDB,
    responses={
        400: {"model": ErrorResponseModel},
        403: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel},
    },
)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    collection=Depends(get_product_collection),
    user=Depends(get_current_user),
):
    """
    Update a product. Only the creator or admin can update.
    Prevents duplicate SKUs and negative values.
    """
    return await product_controller.update_product(
        product_id, product, collection, user
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"model": ErrorResponseModel}, 404: {"model": ErrorResponseModel}},
)
async def delete_product(
    product_id: str,
    collection=Depends(get_product_collection),
    user=Depends(get_current_user),
):
    """
    Soft delete a product. Only the creator or admin can delete.
    """
    return await product_controller.delete_product(product_id, collection, user)


@router.patch(
    "/{product_id}/reactivate",
    response_model=ProductDB,
    responses={403: {"model": ErrorResponseModel}, 404: {"model": ErrorResponseModel}},
)
async def reactivate_product(
    product_id: str,
    collection=Depends(get_product_collection),
    user=Depends(get_current_user),
):
    """
    Reactivate a soft-deleted product. Only admin can reactivate products.
    """
    return await product_controller.reactivate_product(product_id, collection, user)
