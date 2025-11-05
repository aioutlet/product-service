"""
Tests for SizeChartService

Tests for size chart business logic including CRUD operations,
error handling, usage tracking, and template management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.size_chart_service import SizeChartService
from src.models.size_chart import (
    SizeChartFormat,
    RegionalSizing,
    SizeChartEntry,
    CreateSizeChartRequest,
    UpdateSizeChartRequest,
    SizeChartResponse
)
from src.core.errors import ErrorResponse


@pytest.fixture
def mock_repository():
    """Create a mock size chart repository"""
    return AsyncMock()


@pytest.fixture
def service(mock_repository):
    """Create a size chart service with mocked repository"""
    return SizeChartService(mock_repository)


@pytest.fixture
def sample_chart_data():
    """Sample size chart data for testing"""
    return {
        "_id": "chart123",
        "name": "Men's Shirts",
        "category": "Clothing",
        "format": "image",
        "regional_sizing": "us",
        "image_url": "https://example.com/chart.png",
        "description": "Standard men's shirt sizes",
        "is_template": False,
        "is_active": True,
        "applicable_brands": ["Nike", "Adidas"],
        "usage_count": 5,
        "created_by": "user123",
        "updated_by": "user123",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


class TestCreateSizeChart:
    """Test size chart creation"""
    
    @pytest.mark.asyncio
    async def test_create_image_format_chart_success(self, service, mock_repository):
        """Test creating an image format size chart"""
        mock_repository.create.return_value = "chart123"
        
        request = CreateSizeChartRequest(
            name="Test Chart",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png"
        )
        
        chart_id = await service.create_size_chart(request, "user123", "corr123")
        
        assert chart_id == "chart123"
        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args[0][0]
        assert call_args["name"] == "Test Chart"
        assert call_args["format"] == "image"
        assert call_args["image_url"] == "https://example.com/chart.png"
        assert call_args["created_by"] == "user123"
    
    @pytest.mark.asyncio
    async def test_create_json_format_chart_success(self, service, mock_repository):
        """Test creating a JSON format size chart with structured data"""
        mock_repository.create.return_value = "chart456"
        
        entries = [
            SizeChartEntry(size="S", measurements={"chest": "34-36"}),
            SizeChartEntry(size="M", measurements={"chest": "38-40"})
        ]
        
        request = CreateSizeChartRequest(
            name="Structured Chart",
            category="Clothing",
            format=SizeChartFormat.JSON,
            regional_sizing=RegionalSizing.EU,
            structured_data=entries
        )
        
        chart_id = await service.create_size_chart(request, "user456", "corr456")
        
        assert chart_id == "chart456"
        call_args = mock_repository.create.call_args[0][0]
        assert call_args["format"] == "json"
        assert len(call_args["structured_data"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_template_chart(self, service, mock_repository):
        """Test creating a template size chart"""
        mock_repository.create.return_value = "template123"
        
        request = CreateSizeChartRequest(
            name="Template",
            category="Footwear",
            format=SizeChartFormat.PDF,
            regional_sizing=RegionalSizing.UK,
            pdf_url="https://example.com/template.pdf",
            is_template=True
        )
        
        chart_id = await service.create_size_chart(request, "admin1", "corr789")
        
        assert chart_id == "template123"
        call_args = mock_repository.create.call_args[0][0]
        assert call_args["is_template"] is True
    
    @pytest.mark.asyncio
    async def test_create_chart_with_brands(self, service, mock_repository):
        """Test creating size chart with applicable brands"""
        mock_repository.create.return_value = "chart789"
        
        request = CreateSizeChartRequest(
            name="Brand Chart",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png",
            applicable_brands=["Nike", "Adidas", "Puma"]
        )
        
        await service.create_size_chart(request, "user1", "corr1")
        
        call_args = mock_repository.create.call_args[0][0]
        assert call_args["applicable_brands"] == ["Nike", "Adidas", "Puma"]
    
    @pytest.mark.asyncio
    async def test_create_chart_error_handling(self, service, mock_repository):
        """Test error handling during chart creation"""
        mock_repository.create.side_effect = Exception("Database error")
        
        request = CreateSizeChartRequest(
            name="Test",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png"
        )
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.create_size_chart(request, "user1", "corr1")
        
        assert exc_info.value.status_code == 500
        assert "Failed to create size chart" in str(exc_info.value.message)


class TestGetSizeChart:
    """Test retrieving size charts"""
    
    @pytest.mark.asyncio
    async def test_get_chart_success(self, service, mock_repository, sample_chart_data):
        """Test successfully retrieving a size chart"""
        mock_repository.find_by_id.return_value = sample_chart_data
        
        result = await service.get_size_chart("chart123", "corr123")
        
        assert isinstance(result, SizeChartResponse)
        assert result.id == "chart123"
        assert result.name == "Men's Shirts"
        mock_repository.find_by_id.assert_called_once_with("chart123", "corr123")
    
    @pytest.mark.asyncio
    async def test_get_chart_not_found(self, service, mock_repository):
        """Test getting non-existent size chart"""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.get_size_chart("nonexistent", "corr123")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.message)


class TestUpdateSizeChart:
    """Test updating size charts"""
    
    @pytest.mark.asyncio
    async def test_update_chart_success(self, service, mock_repository, sample_chart_data):
        """Test successfully updating a size chart"""
        mock_repository.find_by_id.return_value = sample_chart_data
        updated_data = sample_chart_data.copy()
        updated_data["name"] = "Updated Name"
        mock_repository.update.return_value = updated_data
        
        request = UpdateSizeChartRequest(name="Updated Name")
        
        result = await service.update_size_chart("chart123", request, "user123", "corr123")
        
        assert result.name == "Updated Name"
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_chart_not_found(self, service, mock_repository):
        """Test updating non-existent chart"""
        mock_repository.find_by_id.return_value = None
        
        request = UpdateSizeChartRequest(name="New Name")
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.update_size_chart("nonexistent", request, "user1", "corr1")
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, service, mock_repository, sample_chart_data):
        """Test updating multiple fields at once"""
        mock_repository.find_by_id.return_value = sample_chart_data
        updated_data = sample_chart_data.copy()
        mock_repository.update.return_value = updated_data
        
        request = UpdateSizeChartRequest(
            name="New Name",
            description="New description",
            is_active=False
        )
        
        await service.update_size_chart("chart123", request, "user123", "corr123")
        
        call_args = mock_repository.update.call_args[0][1]
        assert call_args["name"] == "New Name"
        assert call_args["description"] == "New description"
        assert call_args["is_active"] is False
        assert call_args["updated_by"] == "user123"
    
    @pytest.mark.asyncio
    async def test_update_structured_data(self, service, mock_repository, sample_chart_data):
        """Test updating structured data"""
        mock_repository.find_by_id.return_value = sample_chart_data
        updated_data = sample_chart_data.copy()
        mock_repository.update.return_value = updated_data
        
        entries = [SizeChartEntry(size="L", measurements={"chest": "42-44"})]
        request = UpdateSizeChartRequest(structured_data=entries)
        
        await service.update_size_chart("chart123", request, "user123", "corr123")
        
        call_args = mock_repository.update.call_args[0][1]
        assert "structured_data" in call_args
        assert len(call_args["structured_data"]) == 1
    
    @pytest.mark.asyncio
    async def test_update_fails(self, service, mock_repository, sample_chart_data):
        """Test handling update failure"""
        mock_repository.find_by_id.return_value = sample_chart_data
        mock_repository.update.return_value = None
        
        request = UpdateSizeChartRequest(name="New Name")
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.update_size_chart("chart123", request, "user123", "corr123")
        
        assert exc_info.value.status_code == 500


class TestDeleteSizeChart:
    """Test deleting size charts"""
    
    @pytest.mark.asyncio
    async def test_soft_delete_success(self, service, mock_repository, sample_chart_data):
        """Test soft deleting a size chart"""
        mock_repository.find_by_id.return_value = sample_chart_data
        mock_repository.delete.return_value = True
        
        result = await service.delete_size_chart("chart123", True, "user123", "corr123")
        
        assert result is True
        mock_repository.delete.assert_called_once_with("chart123", True, "corr123")
    
    @pytest.mark.asyncio
    async def test_hard_delete_success(self, service, mock_repository, sample_chart_data):
        """Test hard deleting a size chart"""
        chart_data = sample_chart_data.copy()
        chart_data["usage_count"] = 0
        mock_repository.find_by_id.return_value = chart_data
        mock_repository.delete.return_value = True
        
        result = await service.delete_size_chart("chart123", False, "user123", "corr123")
        
        assert result is True
        mock_repository.delete.assert_called_once_with("chart123", False, "corr123")
    
    @pytest.mark.asyncio
    async def test_delete_chart_not_found(self, service, mock_repository):
        """Test deleting non-existent chart"""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.delete_size_chart("nonexistent", True, "user1", "corr1")
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_hard_delete_chart_in_use(self, service, mock_repository, sample_chart_data):
        """Test hard deleting a chart that is in use"""
        chart_data = sample_chart_data.copy()
        chart_data["usage_count"] = 10
        mock_repository.find_by_id.return_value = chart_data
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.delete_size_chart("chart123", False, "user123", "corr123")
        
        assert exc_info.value.status_code == 400
        assert "in use" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_delete_fails(self, service, mock_repository, sample_chart_data):
        """Test handling delete failure"""
        mock_repository.find_by_id.return_value = sample_chart_data
        mock_repository.delete.return_value = False
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.delete_size_chart("chart123", True, "user123", "corr123")
        
        assert exc_info.value.status_code == 500


class TestListSizeCharts:
    """Test listing size charts"""
    
    @pytest.mark.asyncio
    async def test_list_all_charts(self, service, mock_repository, sample_chart_data):
        """Test listing all size charts"""
        mock_repository.list_all.return_value = [sample_chart_data]
        
        result = await service.list_size_charts(correlation_id="corr123")
        
        assert len(result) == 1
        assert result[0].id == "chart123"
        mock_repository.list_all.assert_called_once_with(False, 0, 50, "corr123")
    
    @pytest.mark.asyncio
    async def test_list_by_category(self, service, mock_repository, sample_chart_data):
        """Test listing charts by category"""
        mock_repository.find_by_category.return_value = [sample_chart_data]
        
        result = await service.list_size_charts(
            category="Clothing",
            correlation_id="corr123"
        )
        
        assert len(result) == 1
        mock_repository.find_by_category.assert_called_once_with(
            "Clothing", False, "corr123"
        )
    
    @pytest.mark.asyncio
    async def test_list_with_pagination(self, service, mock_repository):
        """Test listing with pagination parameters"""
        mock_repository.list_all.return_value = []
        
        await service.list_size_charts(skip=10, limit=20, correlation_id="corr123")
        
        mock_repository.list_all.assert_called_once_with(False, 10, 20, "corr123")
    
    @pytest.mark.asyncio
    async def test_list_include_inactive(self, service, mock_repository):
        """Test listing including inactive charts"""
        mock_repository.list_all.return_value = []
        
        await service.list_size_charts(include_inactive=True, correlation_id="corr123")
        
        mock_repository.list_all.assert_called_once_with(True, 0, 50, "corr123")


class TestGetTemplates:
    """Test retrieving templates"""
    
    @pytest.mark.asyncio
    async def test_get_all_templates(self, service, mock_repository, sample_chart_data):
        """Test getting all templates"""
        template_data = sample_chart_data.copy()
        template_data["is_template"] = True
        mock_repository.find_templates.return_value = [template_data]
        
        result = await service.get_templates(correlation_id="corr123")
        
        assert len(result) == 1
        mock_repository.find_templates.assert_called_once_with(None, "corr123")
    
    @pytest.mark.asyncio
    async def test_get_templates_by_category(self, service, mock_repository):
        """Test getting templates filtered by category"""
        mock_repository.find_templates.return_value = []
        
        await service.get_templates(category="Footwear", correlation_id="corr123")
        
        mock_repository.find_templates.assert_called_once_with("Footwear", "corr123")


class TestAssignToProduct:
    """Test assigning size charts to products"""
    
    @pytest.mark.asyncio
    async def test_assign_success(self, service, mock_repository, sample_chart_data):
        """Test successfully assigning chart to product"""
        mock_repository.find_by_id.return_value = sample_chart_data
        mock_repository.increment_usage_count.return_value = True
        
        # Mock the dapr publisher
        with patch('src.services.size_chart_service.get_dapr_publisher') as mock_get_publisher:
            mock_publisher = AsyncMock()
            mock_publisher.publish_sizechart_assigned = AsyncMock(return_value=True)
            mock_get_publisher.return_value = mock_publisher
            
            result = await service.assign_to_product("chart123", "product456", "user123", "corr123")
            
            assert result is True
            mock_repository.increment_usage_count.assert_called_once_with("chart123", "corr123")
            mock_publisher.publish_sizechart_assigned.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_chart_not_found(self, service, mock_repository):
        """Test assigning non-existent chart"""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await service.assign_to_product("nonexistent", "product456", "user123", "corr123")
        
        assert exc_info.value.status_code == 404


class TestUnassignFromProduct:
    """Test unassigning size charts from products"""
    
    @pytest.mark.asyncio
    async def test_unassign_success(self, service, mock_repository):
        """Test successfully unassigning chart from product"""
        mock_repository.decrement_usage_count.return_value = True
        
        # Mock the dapr publisher
        with patch('src.services.size_chart_service.get_dapr_publisher') as mock_get_publisher:
            mock_publisher = AsyncMock()
            mock_publisher.publish_sizechart_unassigned = AsyncMock(return_value=True)
            mock_get_publisher.return_value = mock_publisher
            
            result = await service.unassign_from_product("chart123", "product456", "user123", "corr123")
            
            assert result is True
            mock_repository.decrement_usage_count.assert_called_once_with("chart123", "corr123")
            mock_publisher.publish_sizechart_unassigned.assert_called_once()

