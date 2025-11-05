"""
Product Variation API Endpoints

Handles parent-child product relationships and variant management.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Optional

from src.dependencies.auth import CurrentUser, get_current_user, require_admin
from src.dependencies import get_products_collection, get_product_repository
from src.services.variation_service import VariationService
from src.repositories.product_repository import ProductRepository
from src.models.variation import (
    CreateVariationRequest,
    UpdateVariationRequest,
    VariationRelationship,
    BulkCreateVariationsRequest,
    BulkCreateVariationsResponse
)
from src.core.errors import ErrorResponseModel
from motor.motor_asyncio import AsyncIOMotorCollection


router = APIRouter(prefix="/variations", tags=["variations"])


def get_variation_service(
    collection: AsyncIOMotorCollection = Depends(get_products_collection)
) -> VariationService:
    """Get variation service instance."""
    repo = ProductRepository(collection)
    return VariationService(repo)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel},
        409: {"model": ErrorResponseModel}
    }
)
async def create_variation(
    request: CreateVariationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: VariationService = Depends(get_variation_service)
):
    """
    Create a child variation product.
    
    Requires admin role.
    
    **Parent Product Requirements:**
    - Must have `variation_type` set to `"parent"`
    - Must exist and be active
    
    **Variant Attributes:**
    - At least one variant attribute required
    - Common attributes: color, size, material, style
    - Example: `[{"name": "color", "value": "red"}, {"name": "size", "value": "XL"}]`
    
    **Pricing:**
    - Can override parent's price or inherit it
    - `compare_at_price` for showing discounts
    
    **Inventory:**
    - Each variation has independent inventory (default mode)
    - Or shared inventory with parent (configure on parent)
    """
    variation_id = await service.create_variation(
        request=request,
        acting_user=current_user.user_id,
        correlation_id=None  # TODO: Extract from request headers
    )
    
    return {
        "id": variation_id,
        "parent_id": request.parent_id,
        "sku": request.sku,
        "message": "Variation created successfully"
    }


@router.put(
    "/{variation_id}",
    response_model=dict,
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel}
    }
)
async def update_variation(
    variation_id: str,
    request: UpdateVariationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: VariationService = Depends(get_variation_service)
):
    """
    Update a child variation product.
    
    Requires admin role.
    
    **Updatable Fields:**
    - name, price, compare_at_price
    - description, images
    - variant_attributes (must still be valid for parent)
    - stock_quantity, is_active
    
    **Notes:**
    - Cannot change parent_id after creation
    - Variant attributes must still match parent's configuration
    """
    updated = await service.update_variation(
        variation_id=variation_id,
        request=request,
        acting_user=current_user.user_id,
        correlation_id=None
    )
    
    return {
        "id": variation_id,
        "message": "Variation updated successfully",
        "product": updated
    }


@router.get(
    "/{product_id}/relationship",
    response_model=VariationRelationship,
    responses={404: {"model": ErrorResponseModel}}
)
async def get_variation_relationship(
    product_id: str,
    service: VariationService = Depends(get_variation_service)
):
    """
    Get complete variation relationship for a product.
    
    **Behavior:**
    - If product is a **parent**: Returns parent + all child variations
    - If product is a **child**: Returns its parent + all sibling variations
    - If product is **standalone**: Returns just the product
    
    **Response includes:**
    - Parent product summary
    - List of all child variations
    - Attribute matrix showing all combinations
    - Price ranges across all variations
    - Availability status for each variation
    
    **Use Cases:**
    - Product detail page showing all available variants
    - Admin interface for managing variations
    - Inventory management across variations
    """
    return await service.get_variation_relationship(
        product_id=product_id,
        correlation_id=None
    )


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=BulkCreateVariationsResponse,
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ErrorResponseModel},
        404: {"model": ErrorResponseModel}
    }
)
async def bulk_create_variations(
    request: BulkCreateVariationsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: VariationService = Depends(get_variation_service)
):
    """
    Create multiple variations in bulk.
    
    Requires admin role.
    
    **Use Cases:**
    - Create all size/color combinations at once
    - Import variations from spreadsheet
    - Set up complete product line with variations
    
    **Auto-Generate Names:**
    - Set `auto_generate_names: true` to automatically generate names
    - Format: `{Parent Name} - {Attribute Values}`
    - Example: "T-Shirt - Red, XL"
    
    **Partial Success:**
    - Some variations may succeed while others fail
    - Response includes detailed error information per variation
    - Successfully created variations are committed even if others fail
    
    **Response:**
    - `success_count`: Number of variations created
    - `failure_count`: Number that failed
    - `created_ids`: IDs of successfully created variations
    - `errors`: Detailed error for each failure (includes variation_index)
    """
    return await service.bulk_create_variations(
        request=request,
        acting_user=current_user.user_id,
        correlation_id=None
    )


@router.get(
    "/parent/{parent_id}/children",
    response_model=dict,
    responses={404: {"model": ErrorResponseModel}}
)
async def get_parent_children(
    parent_id: str,
    include_inactive: bool = False,
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Get all children of a parent product.
    
    **Query Parameters:**
    - `include_inactive`: Include inactive/archived child variations (default: false)
    
    **Use Cases:**
    - List all available variations for a product
    - Product selection dropdown
    - Inventory management
    
    **Returns:**
    - List of child products with variant attributes
    - Sorted by creation date
    """
    query = {"parent_id": parent_id}
    if not include_inactive:
        query["is_active"] = True
    
    children = await repo.find_many(query, correlation_id=None)
    
    return {
        "parent_id": parent_id,
        "child_count": len(children),
        "children": children
    }


@router.delete(
    "/{variation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
    responses={404: {"model": ErrorResponseModel}}
)
async def delete_variation(
    variation_id: str,
    hard_delete: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    service: VariationService = Depends(get_variation_service)
):
    """
    Delete a child variation (soft delete by default).
    
    Requires admin role.
    
    **Query Parameters:**
    - `hard_delete`: Permanently delete (default: false, soft delete)
    
    **Soft Delete:**
    - Sets `is_active` to false
    - Product remains in database
    - Can be reactivated later
    - Updates parent's child_count
    
    **Hard Delete:**
    - Permanently removes from database
    - Cannot be recovered
    - Updates parent's child_skus and child_count
    
    **Note:** Cannot delete if it's the last active variation
    """
    # For now, just update to inactive (soft delete)
    await service.update_variation(
        variation_id=variation_id,
        request=UpdateVariationRequest(is_active=False),
        acting_user=current_user.user_id,
        correlation_id=None
    )
    
    return None
