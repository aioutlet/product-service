"""
Size Chart API Endpoints

REST API endpoints for size chart management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from src.models.size_chart import (
    CreateSizeChartRequest,
    UpdateSizeChartRequest,
    SizeChartResponse,
    SizeChartSummary
)
from src.services.size_chart_service import SizeChartService
from src.dependencies import (
    get_size_chart_service,
    get_correlation_id,
    get_current_user
)
from src.auth.models import CurrentUser


router = APIRouter(prefix="/api/size-charts", tags=["size-charts"])


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new size chart",
    description="Create a new size chart. Requires admin role."
)
async def create_size_chart(
    request: CreateSizeChartRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Create a new size chart.
    
    **Required Role:** admin
    
    Args:
        request: Size chart creation request
        current_user: Current authenticated user
        service: Size chart service
        correlation_id: Request correlation ID
        
    Returns:
        Created size chart ID
    """
    # Check admin role
    if "admin" not in current_user.roles:
        from src.core.errors import ErrorResponse
        raise ErrorResponse(
            "Admin role required to create size charts",
            status_code=403
        )
    
    size_chart_id = await service.create_size_chart(
        request,
        current_user.user_id,
        correlation_id
    )
    
    return {
        "size_chart_id": size_chart_id,
        "message": "Size chart created successfully"
    }


@router.get(
    "",
    response_model=List[SizeChartSummary],
    summary="List size charts",
    description="List all size charts with optional filtering and pagination."
)
async def list_size_charts(
    category: Optional[str] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False, description="Include inactive charts"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    List size charts with optional filtering.
    
    Args:
        category: Optional category filter
        include_inactive: Include inactive charts
        skip: Pagination offset
        limit: Maximum results
        service: Size chart service
        correlation_id: Request correlation ID
        
    Returns:
        List of size chart summaries
    """
    return await service.list_size_charts(
        category,
        include_inactive,
        skip,
        limit,
        correlation_id
    )


@router.get(
    "/templates",
    response_model=List[SizeChartResponse],
    summary="Get size chart templates",
    description="Get available size chart templates, optionally filtered by category."
)
async def get_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get available size chart templates.
    
    Args:
        category: Optional category filter
        service: Size chart service
        correlation_id: Request correlation ID
        
    Returns:
        List of size chart templates
    """
    return await service.get_templates(category, correlation_id)


@router.get(
    "/category/{category}",
    response_model=List[SizeChartSummary],
    summary="Get size charts by category",
    description="Get all size charts for a specific category."
)
async def get_by_category(
    category: str,
    include_inactive: bool = Query(False, description="Include inactive charts"),
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get size charts by category.
    
    Args:
        category: Product category
        include_inactive: Include inactive charts
        service: Size chart service
        correlation_id: Request correlation ID
        
    Returns:
        List of size charts for the category
    """
    charts = await service.list_size_charts(
        category=category,
        include_inactive=include_inactive,
        skip=0,
        limit=100,
        correlation_id=correlation_id
    )
    return charts


@router.get(
    "/{size_chart_id}",
    response_model=SizeChartResponse,
    summary="Get size chart by ID",
    description="Retrieve a specific size chart by its ID."
)
async def get_size_chart(
    size_chart_id: str,
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get size chart by ID.
    
    Args:
        size_chart_id: Size chart ID
        service: Size chart service
        correlation_id: Request correlation ID
        
    Returns:
        Size chart details
    """
    return await service.get_size_chart(size_chart_id, correlation_id)


@router.put(
    "/{size_chart_id}",
    response_model=SizeChartResponse,
    summary="Update a size chart",
    description="Update an existing size chart. Requires admin role."
)
async def update_size_chart(
    size_chart_id: str,
    request: UpdateSizeChartRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Update an existing size chart.
    
    **Required Role:** admin
    
    Args:
        size_chart_id: Size chart ID
        request: Update request
        current_user: Current authenticated user
        service: Size chart service
        correlation_id: Request correlation ID
        
    Returns:
        Updated size chart
    """
    # Check admin role
    if "admin" not in current_user.roles:
        from src.core.errors import ErrorResponse
        raise ErrorResponse(
            "Admin role required to update size charts",
            status_code=403
        )
    
    return await service.update_size_chart(
        size_chart_id,
        request,
        current_user.user_id,
        correlation_id
    )


@router.delete(
    "/{size_chart_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a size chart",
    description="Delete a size chart. By default performs soft delete. Requires admin role."
)
async def delete_size_chart(
    size_chart_id: str,
    soft_delete: bool = Query(True, description="Soft delete (set inactive) or hard delete"),
    current_user: CurrentUser = Depends(get_current_user),
    service: SizeChartService = Depends(get_size_chart_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Delete a size chart.
    
    **Required Role:** admin
    
    Args:
        size_chart_id: Size chart ID
        soft_delete: Whether to soft delete (default: True)
        current_user: Current authenticated user
        service: Size chart service
        correlation_id: Request correlation ID
    """
    # Check admin role
    if "admin" not in current_user.roles:
        from src.core.errors import ErrorResponse
        raise ErrorResponse(
            "Admin role required to delete size charts",
            status_code=403
        )
    
    await service.delete_size_chart(
        size_chart_id,
        soft_delete,
        current_user.user_id,
        correlation_id
    )
