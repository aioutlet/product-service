"""
Product Variation Router
Implements PRD REQ-8.1 to REQ-8.5: Product Variations API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict

from src.models.variation_models import (
    ParentProductCreate,
    ParentProductResponse,
    AddVariationRequest,
    VariationUpdate,
    VariationFilterRequest,
    VariationMatrix
)
from src.services.variation_service import get_variation_service
from src.security import require_admin
from src.observability import logger

router = APIRouter()


@router.post(
    '/parent-products',
    response_model=Dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create parent product with variations",
    description="Create parent product with all variations in single operation (REQ-8.5)"
)
async def create_parent_with_variations(
    parent_data: ParentProductCreate,
    user=Depends(require_admin)
):
    """
    Create parent product with variations (REQ-8.5)
    
    - Supports up to 1,000 variations per parent
    - Validates SKU uniqueness
    - Validates variation attribute uniqueness
    - Admin-only operation
    """
    try:
        variation_service = get_variation_service()
        result = await variation_service.create_parent_with_variations(
            parent_data=parent_data,
            created_by=user.user_id
        )
        
        logger.info(
            f"Parent product created by admin: {result['parent_id']}",
            metadata={
                'event': 'admin_parent_product_created',
                'userId': user.user_id,
                'parentId': result['parent_id'],
                'variationCount': result['variation_count']
            }
        )
        
        return {
            'message': 'Parent product created successfully',
            'parent_id': result['parent_id'],
            'variation_ids': result['variation_ids'],
            'variation_count': result['variation_count']
        }
    
    except ValueError as e:
        logger.warning(
            f"Validation error creating parent product: {str(e)}",
            metadata={
                'event': 'parent_product_validation_error',
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Error creating parent product: {str(e)}",
            metadata={
                'event': 'parent_product_creation_error',
                'error': str(e),
                'errorType': type(e).__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create parent product"
        )


@router.get(
    '/parent-products/{parent_id}',
    response_model=ParentProductResponse,
    summary="Get parent product with variations",
    description="Get parent product with all variations and variation matrix (REQ-8.4)"
)
async def get_parent_with_variations(parent_id: str):
    """
    Get parent product with all variations (REQ-8.4)
    
    Returns:
    - Parent product details
    - All available variations
    - Variation matrix with availability
    """
    try:
        variation_service = get_variation_service()
        parent = await variation_service.get_parent_with_variations(
            parent_id=parent_id
        )
        
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent product {parent_id} not found"
            )
        
        return parent
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting parent product: {str(e)}",
            metadata={
                'event': 'get_parent_product_error',
                'parentId': parent_id,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get parent product"
        )


@router.post(
    '/parent-products/{parent_id}/variations',
    response_model=Dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add variation to parent product",
    description="Add new variation to existing parent product (REQ-8.5)"
)
async def add_variation(
    parent_id: str,
    request: AddVariationRequest,
    user=Depends(require_admin)
):
    """
    Add new variation to existing parent (REQ-8.5)
    
    - Validates SKU uniqueness
    - Validates attribute combination uniqueness
    - Admin-only operation
    """
    try:
        variation_service = get_variation_service()
        variation_id = await variation_service.add_variation_to_parent(
            parent_id=parent_id,
            variation=request.variation,
            created_by=user.user_id
        )
        
        logger.info(
            f"Variation added to parent {parent_id}",
            metadata={
                'event': 'admin_variation_added',
                'userId': user.user_id,
                'parentId': parent_id,
                'variationId': variation_id
            }
        )
        
        return {
            'message': 'Variation added successfully',
            'variation_id': variation_id,
            'parent_id': parent_id
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Error adding variation: {str(e)}",
            metadata={
                'event': 'add_variation_error',
                'parentId': parent_id,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add variation"
        )


@router.put(
    '/variations/{variation_id}',
    response_model=Dict,
    summary="Update variation",
    description="Update variation attributes (REQ-8.5)"
)
async def update_variation(
    variation_id: str,
    updates: VariationUpdate,
    user=Depends(require_admin)
):
    """
    Update variation attributes (REQ-8.5)
    
    - Can update price, attributes, images, etc.
    - Admin-only operation
    """
    try:
        variation_service = get_variation_service()
        success = await variation_service.update_variation(
            variation_id=variation_id,
            updates=updates,
            updated_by=user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variation {variation_id} not found"
            )
        
        logger.info(
            f"Variation updated: {variation_id}",
            metadata={
                'event': 'admin_variation_updated',
                'userId': user.user_id,
                'variationId': variation_id
            }
        )
        
        return {
            'message': 'Variation updated successfully',
            'variation_id': variation_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating variation: {str(e)}",
            metadata={
                'event': 'update_variation_error',
                'variationId': variation_id,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update variation"
        )


@router.delete(
    '/variations/{variation_id}',
    response_model=Dict,
    summary="Delete variation",
    description="Soft delete variation (REQ-8.5)"
)
async def delete_variation(
    variation_id: str,
    user=Depends(require_admin)
):
    """
    Soft delete variation (REQ-8.5)
    
    - Sets is_active to False
    - Updates parent variation count
    - Admin-only operation
    """
    try:
        variation_service = get_variation_service()
        success = await variation_service.delete_variation(
            variation_id=variation_id,
            deleted_by=user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variation {variation_id} not found"
            )
        
        logger.info(
            f"Variation deleted: {variation_id}",
            metadata={
                'event': 'admin_variation_deleted',
                'userId': user.user_id,
                'variationId': variation_id
            }
        )
        
        return {
            'message': 'Variation deleted successfully',
            'variation_id': variation_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting variation: {str(e)}",
            metadata={
                'event': 'delete_variation_error',
                'variationId': variation_id,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete variation"
        )


@router.post(
    '/parent-products/{parent_id}/variations/filter',
    response_model=List[VariationMatrix],
    summary="Filter variations by attributes",
    description="Filter variations by attribute values (REQ-8.4)"
)
async def filter_variations(
    parent_id: str,
    filter_request: VariationFilterRequest
):
    """
    Filter variations by attribute values (REQ-8.4)
    
    Example:
    - Filter by color: {"attributes": {"color": "Black"}}
    - Filter by color and size: {"attributes": {"color": "Black", "size": "M"}}
    """
    try:
        variation_service = get_variation_service()
        variations = await variation_service.filter_variations(
            parent_id=parent_id,
            attribute_filters=filter_request.attributes
        )
        
        return variations
    
    except Exception as e:
        logger.error(
            f"Error filtering variations: {str(e)}",
            metadata={
                'event': 'filter_variations_error',
                'parentId': parent_id,
                'filters': filter_request.attributes,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter variations"
        )
