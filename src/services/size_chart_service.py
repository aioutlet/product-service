"""
Size Chart Service

Business logic for size chart management including CRUD operations,
template management, and size chart assignment to products.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from src.repositories.size_chart_repository import SizeChartRepository
from src.services.dapr_publisher import get_dapr_publisher
from src.models.size_chart import (
    CreateSizeChartRequest,
    UpdateSizeChartRequest,
    SizeChartResponse,
    SizeChartSummary,
    SizeChartTemplate
)
from src.core.errors import ErrorResponse
from src.core.logger import logger


class SizeChartService:
    """Service for size chart operations"""
    
    def __init__(self, repository: SizeChartRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Size chart repository instance
        """
        self.repository = repository
    
    async def create_size_chart(
        self,
        request: CreateSizeChartRequest,
        acting_user: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Create a new size chart.
        
        Args:
            request: Size chart creation request
            acting_user: ID of user creating the chart
            correlation_id: Request correlation ID
            
        Returns:
            Created size chart ID
            
        Raises:
            ErrorResponse: If creation fails
        """
        try:
            # Prepare size chart data
            chart_data = {
                "name": request.name,
                "category": request.category,
                "format": request.format.value,
                "regional_sizing": request.regional_sizing.value,
                "description": request.description,
                "is_template": request.is_template,
                "applicable_brands": request.applicable_brands or [],
                "created_by": acting_user,
                "updated_by": acting_user
            }
            
            # Add format-specific data
            if request.image_url:
                chart_data["image_url"] = request.image_url
            if request.pdf_url:
                chart_data["pdf_url"] = request.pdf_url
            if request.structured_data:
                chart_data["structured_data"] = [
                    entry.model_dump() for entry in request.structured_data
                ]
            
            # Create in database
            chart_id = await self.repository.create(chart_data, correlation_id)
            
            logger.info(
                "Size chart created",
                metadata={
                    "size_chart_id": chart_id,
                    "category": request.category,
                    "format": request.format.value,
                    "acting_user": acting_user,
                    "correlation_id": correlation_id
                }
            )
            
            return chart_id
            
        except Exception as e:
            logger.error(
                "Error creating size chart",
                error=e,
                metadata={"acting_user": acting_user, "correlation_id": correlation_id}
            )
            raise ErrorResponse(
                f"Failed to create size chart: {str(e)}",
                status_code=500
            )
    
    async def get_size_chart(
        self,
        size_chart_id: str,
        correlation_id: Optional[str] = None
    ) -> SizeChartResponse:
        """
        Get size chart by ID.
        
        Args:
            size_chart_id: Size chart ID
            correlation_id: Request correlation ID
            
        Returns:
            Size chart response
            
        Raises:
            ErrorResponse: If chart not found
        """
        chart = await self.repository.find_by_id(size_chart_id, correlation_id)
        
        if not chart:
            raise ErrorResponse(
                f"Size chart with ID {size_chart_id} not found",
                status_code=404
            )
        
        return SizeChartResponse(**chart)
    
    async def update_size_chart(
        self,
        size_chart_id: str,
        request: UpdateSizeChartRequest,
        acting_user: str,
        correlation_id: Optional[str] = None
    ) -> SizeChartResponse:
        """
        Update an existing size chart.
        
        Args:
            size_chart_id: Size chart ID to update
            request: Update request with fields to change
            acting_user: ID of user updating the chart
            correlation_id: Request correlation ID
            
        Returns:
            Updated size chart
            
        Raises:
            ErrorResponse: If chart not found or update fails
        """
        # Check if chart exists
        existing = await self.repository.find_by_id(size_chart_id, correlation_id)
        if not existing:
            raise ErrorResponse(
                f"Size chart with ID {size_chart_id} not found",
                status_code=404
            )
        
        # Build update data
        update_data = {"updated_by": acting_user}
        
        if request.name is not None:
            update_data["name"] = request.name
        if request.category is not None:
            update_data["category"] = request.category
        if request.description is not None:
            update_data["description"] = request.description
        if request.image_url is not None:
            update_data["image_url"] = request.image_url
        if request.pdf_url is not None:
            update_data["pdf_url"] = request.pdf_url
        if request.structured_data is not None:
            update_data["structured_data"] = [
                entry.model_dump() for entry in request.structured_data
            ]
        if request.applicable_brands is not None:
            update_data["applicable_brands"] = request.applicable_brands
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        # Perform update
        updated = await self.repository.update(
            size_chart_id,
            update_data,
            correlation_id
        )
        
        if not updated:
            raise ErrorResponse(
                "Failed to update size chart",
                status_code=500
            )
        
        logger.info(
            "Size chart updated",
            metadata={
                "size_chart_id": size_chart_id,
                "acting_user": acting_user,
                "correlation_id": correlation_id
            }
        )
        
        return SizeChartResponse(**updated)
    
    async def delete_size_chart(
        self,
        size_chart_id: str,
        soft_delete: bool = True,
        acting_user: str = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Delete a size chart.
        
        Args:
            size_chart_id: Size chart ID to delete
            soft_delete: Whether to soft delete (set is_active=False)
            acting_user: ID of user deleting the chart
            correlation_id: Request correlation ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            ErrorResponse: If chart not found or delete fails
        """
        # Check if chart exists
        existing = await self.repository.find_by_id(size_chart_id, correlation_id)
        if not existing:
            raise ErrorResponse(
                f"Size chart with ID {size_chart_id} not found",
                status_code=404
            )
        
        # Check if chart is in use
        if existing.get("usage_count", 0) > 0 and not soft_delete:
            raise ErrorResponse(
                f"Cannot delete size chart that is in use by {existing['usage_count']} products. Use soft delete instead.",
                status_code=400
            )
        
        success = await self.repository.delete(
            size_chart_id,
            soft_delete,
            correlation_id
        )
        
        if not success:
            raise ErrorResponse(
                "Failed to delete size chart",
                status_code=500
            )
        
        logger.info(
            "Size chart deleted",
            metadata={
                "size_chart_id": size_chart_id,
                "soft_delete": soft_delete,
                "acting_user": acting_user,
                "correlation_id": correlation_id
            }
        )
        
        return True
    
    async def list_size_charts(
        self,
        category: Optional[str] = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
        correlation_id: Optional[str] = None
    ) -> List[SizeChartSummary]:
        """
        List size charts with optional filtering.
        
        Args:
            category: Optional category filter
            include_inactive: Include inactive charts
            skip: Number of records to skip
            limit: Maximum records to return
            correlation_id: Request correlation ID
            
        Returns:
            List of size chart summaries
        """
        if category:
            charts = await self.repository.find_by_category(
                category,
                include_inactive,
                correlation_id
            )
        else:
            charts = await self.repository.list_all(
                include_inactive,
                skip,
                limit,
                correlation_id
            )
        
        return [SizeChartSummary(**chart) for chart in charts]
    
    async def get_templates(
        self,
        category: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[SizeChartResponse]:
        """
        Get available size chart templates.
        
        Args:
            category: Optional category filter
            correlation_id: Request correlation ID
            
        Returns:
            List of size chart templates
        """
        templates = await self.repository.find_templates(category, correlation_id)
        return [SizeChartResponse(**template) for template in templates]
    
    async def assign_to_product(
        self,
        size_chart_id: str,
        product_id: str,
        assigned_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Assign size chart to a product and increment usage count.
        
        Args:
            size_chart_id: Size chart ID
            product_id: Product ID
            assigned_by: User ID who assigned the size chart
            correlation_id: Request correlation ID
            
        Returns:
            True if assigned successfully
            
        Raises:
            ErrorResponse: If size chart not found
        """
        # Check if size chart exists
        chart = await self.repository.find_by_id(size_chart_id, correlation_id)
        if not chart:
            raise ErrorResponse(
                f"Size chart with ID {size_chart_id} not found",
                status_code=404
            )
        
        # Increment usage count
        success = await self.repository.increment_usage_count(
            size_chart_id,
            correlation_id
        )
        
        if success:
            logger.info(
                "Size chart assigned to product",
                metadata={
                    "size_chart_id": size_chart_id,
                    "product_id": product_id,
                    "correlation_id": correlation_id
                }
            )
            
            # Publish sizechart.assigned event
            try:
                publisher = get_dapr_publisher()
                await publisher.publish_sizechart_assigned(
                    size_chart_id=size_chart_id,
                    product_ids=[product_id],
                    assigned_by=assigned_by,
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.error(
                    f"Failed to publish sizechart.assigned event: {str(e)}",
                    metadata={"size_chart_id": size_chart_id, "product_id": product_id}
                )
        
        return success
    
    async def unassign_from_product(
        self,
        size_chart_id: str,
        product_id: str,
        unassigned_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Unassign size chart from a product and decrement usage count.
        
        Args:
            size_chart_id: Size chart ID
            product_id: Product ID
            unassigned_by: User ID who unassigned the size chart
            correlation_id: Request correlation ID
            
        Returns:
            True if unassigned successfully
        """
        # Decrement usage count
        success = await self.repository.decrement_usage_count(
            size_chart_id,
            correlation_id
        )
        
        if success:
            logger.info(
                "Size chart unassigned from product",
                metadata={
                    "size_chart_id": size_chart_id,
                    "product_id": product_id,
                    "correlation_id": correlation_id
                }
            )
            
            # Publish sizechart.unassigned event
            try:
                publisher = get_dapr_publisher()
                await publisher.publish_sizechart_unassigned(
                    size_chart_id=size_chart_id,
                    product_ids=[product_id],
                    unassigned_by=unassigned_by,
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.error(
                    f"Failed to publish sizechart.unassigned event: {str(e)}",
                    metadata={"size_chart_id": size_chart_id, "product_id": product_id}
                )
        
        return success
