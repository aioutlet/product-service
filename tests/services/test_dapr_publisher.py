"""Unit tests for Dapr publisher service"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.dapr_publisher import DaprPublisher, get_dapr_publisher


class TestDaprPublisher:
    """Test cases for DaprPublisher class"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response"""
        response = MagicMock()
        response.status_code = 204
        response.text = ""
        return response
    
    @pytest.fixture
    def dapr_publisher(self):
        """Create DaprPublisher instance"""
        return DaprPublisher()
    
    @pytest.mark.asyncio
    async def test_publish_success(self, dapr_publisher, mock_response):
        """Test successful event publishing"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            test_data = {
                "productId": "test-123",
                "name": "Test Product",
                "price": 29.99
            }
            
            # Act
            result = await dapr_publisher.publish(
                topic="product.created",
                data=test_data,
                event_type="com.aioutlet.product.created.v1",
                correlation_id="test-correlation-123"
            )
            
            # Assert
            assert result is True
            mock_client.post.assert_called_once()
            
            # Verify the URL and payload
            call_args = mock_client.post.call_args
            assert "product.created" in call_args[0][0]  # URL contains topic
            
            # Verify CloudEvents structure
            payload = call_args[1]["json"]
            assert payload["specversion"] == "1.0"
            assert payload["type"] == "com.aioutlet.product.created.v1"
            assert payload["data"] == test_data
            assert payload["correlationid"] == "test-correlation-123"
    
    @pytest.mark.asyncio
    async def test_publish_failure(self, dapr_publisher):
        """Test failed event publishing"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            test_data = {"productId": "test-123"}
            
            # Act
            result = await dapr_publisher.publish(
                topic="product.created",
                data=test_data,
                event_type="com.aioutlet.product.created.v1"
            )
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_publish_with_exception(self, dapr_publisher):
        """Test event publishing with network exception"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))
            mock_client_class.return_value = mock_client
            
            test_data = {"productId": "test-123"}
            
            # Act
            result = await dapr_publisher.publish(
                topic="product.created",
                data=test_data,
                event_type="com.aioutlet.product.created.v1"
            )
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_publish_product_created(self, dapr_publisher, mock_response):
        """Test convenience method for product.created event"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            product = {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Test Product",
                "sku": "TEST-001",
                "price": 29.99,
                "brand": "Test Brand",
                "category": "Test Category"
            }
            
            # Act
            result = await dapr_publisher.publish_product_created(
                product=product,
                acting_user="user123",
                correlation_id="test-correlation"
            )
            
            # Assert
            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            
            # Verify CloudEvents structure
            payload = call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.created.v1"
            assert payload["data"]["product"] == product
            assert payload["data"]["actingUser"] == "user123"
    
    @pytest.mark.asyncio
    async def test_publish_product_updated(self, dapr_publisher, mock_response):
        """Test convenience method for product.updated event"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            product = {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Updated Product",
                "price": 39.99
            }
            
            changes = {"price": {"old": 29.99, "new": 39.99}}
            
            # Act
            result = await dapr_publisher.publish_product_updated(
                product=product,
                changes=changes,
                acting_user="admin123"
            )
            
            # Assert
            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            
            # Verify CloudEvents structure
            payload = call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.updated.v1"
            assert payload["data"]["product"] == product
            assert payload["data"]["changes"] == changes
            assert payload["data"]["actingUser"] == "admin123"
    
    @pytest.mark.asyncio
    async def test_publish_product_deleted(self, dapr_publisher, mock_response):
        """Test convenience method for product.deleted event"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await dapr_publisher.publish_product_deleted(
                product_id="507f1f77bcf86cd799439011",
                sku="TEST-001",
                acting_user="admin123"
            )
            
            # Assert
            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            
            # Verify CloudEvents structure
            payload = call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.deleted.v1"
            assert "507f1f77bcf86cd799439011" in str(payload["data"])
    
    def test_get_dapr_publisher_singleton(self):
        """Test that get_dapr_publisher returns singleton instance"""
        # Act
        publisher1 = get_dapr_publisher()
        publisher2 = get_dapr_publisher()
        
        # Assert
        assert publisher1 is publisher2
    
    @pytest.mark.asyncio
    async def test_publish_without_correlation_id(self, dapr_publisher, mock_response):
        """Test publishing without correlation ID"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await dapr_publisher.publish(
                topic="product.created",
                data={"test": "data"},
                event_type="com.aioutlet.product.created.v1"
            )
            
            # Assert
            assert result is True
            call_args = mock_client.post.call_args
            
            # Verify event was published (correlation ID is optional)
            payload = call_args[1]["json"]
            assert payload["data"] == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_publish_with_correlation_id(self, dapr_publisher, mock_response):
        """Test publishing with correlation ID"""
        # Arrange
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await dapr_publisher.publish(
                topic="product.created",
                data={"test": "data"},
                event_type="com.aioutlet.product.created.v1",
                correlation_id="custom-correlation-id"
            )
            
            # Assert
            assert result is True
            call_args = mock_client.post.call_args
            
            # Verify correlation ID was included
            payload = call_args[1]["json"]
            assert payload["correlationid"] == "custom-correlation-id"


class TestBadgeEvents:
    """Test badge event publishing"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response"""
        response = MagicMock()
        response.status_code = 204
        return response
    
    @pytest.fixture
    def dapr_publisher(self):
        """Create DaprPublisher instance"""
        return DaprPublisher()
    
    @pytest.mark.asyncio
    async def test_publish_badge_assigned(self, dapr_publisher, mock_response):
        """Test badge.assigned event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_badge_assigned(
                product_id="prod123",
                badge_type="best_seller",
                expires_at="2025-12-31T23:59:59Z",
                assigned_by="user123",
                automated=False,
                correlation_id="corr-123"
            )
            
            assert result is True
            call_args = mock_client.post.call_args
            assert "product.badge.assigned" in call_args[0][0]
            
            payload = call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.badge.assigned.v1"
            assert payload["data"]["productId"] == "prod123"
            assert payload["data"]["badgeType"] == "best_seller"
            assert payload["data"]["automated"] is False
    
    @pytest.mark.asyncio
    async def test_publish_badge_removed(self, dapr_publisher, mock_response):
        """Test badge.removed event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_badge_removed(
                product_id="prod123",
                badge_type="best_seller",
                removed_by="user123",
                reason="expired",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.badge.removed.v1"
            assert payload["data"]["reason"] == "expired"


class TestVariationEvents:
    """Test variation event publishing"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response"""
        response = MagicMock()
        response.status_code = 204
        return response
    
    @pytest.fixture
    def dapr_publisher(self):
        """Create DaprPublisher instance"""
        return DaprPublisher()
    
    @pytest.mark.asyncio
    async def test_publish_variation_created(self, dapr_publisher, mock_response):
        """Test variation.created event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_variation_created(
                parent_id="parent123",
                variation_id="child456",
                variation_type="color",
                variant_attributes={"color": "red", "size": "M"},
                created_by="user123",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.variation.created.v1"
            assert payload["data"]["parentId"] == "parent123"
            assert payload["data"]["variantAttributes"] == {"color": "red", "size": "M"}
    
    @pytest.mark.asyncio
    async def test_publish_variation_updated(self, dapr_publisher, mock_response):
        """Test variation.updated event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_variation_updated(
                parent_id="parent123",
                variation_id="child456",
                changes={"price": 29.99},
                updated_by="user123",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.variation.updated.v1"
            assert payload["data"]["changes"] == {"price": 29.99}
    
    @pytest.mark.asyncio
    async def test_publish_variation_deleted(self, dapr_publisher, mock_response):
        """Test variation.deleted event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_variation_deleted(
                parent_id="parent123",
                variation_id="child456",
                deleted_by="user123",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.variation.deleted.v1"


class TestSizeChartEvents:
    """Test size chart event publishing"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response"""
        response = MagicMock()
        response.status_code = 204
        return response
    
    @pytest.fixture
    def dapr_publisher(self):
        """Create DaprPublisher instance"""
        return DaprPublisher()
    
    @pytest.mark.asyncio
    async def test_publish_sizechart_assigned(self, dapr_publisher, mock_response):
        """Test sizechart.assigned event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_sizechart_assigned(
                size_chart_id="sc123",
                product_ids=["prod1", "prod2"],
                assigned_by="user123",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.sizechart.assigned.v1"
            assert payload["data"]["sizeChartId"] == "sc123"
            assert payload["data"]["productCount"] == 2
    
    @pytest.mark.asyncio
    async def test_publish_sizechart_unassigned(self, dapr_publisher, mock_response):
        """Test sizechart.unassigned event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_sizechart_unassigned(
                size_chart_id="sc123",
                product_ids=["prod1"],
                unassigned_by="user123",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.sizechart.unassigned.v1"
            assert payload["data"]["productCount"] == 1


class TestBulkOperationEvents:
    """Test bulk operation event publishing"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response"""
        response = MagicMock()
        response.status_code = 204
        return response
    
    @pytest.fixture
    def dapr_publisher(self):
        """Create DaprPublisher instance"""
        return DaprPublisher()
    
    @pytest.mark.asyncio
    async def test_publish_bulk_operation_completed(self, dapr_publisher, mock_response):
        """Test bulk.completed event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_bulk_operation_completed(
                operation="create",
                success_count=45,
                failure_count=5,
                total_count=50,
                operation_id="bulk-123",
                executed_by="user123",
                details={"skus": ["SKU1"]},
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.bulk.completed.v1"
            assert payload["data"]["successCount"] == 45
            assert payload["data"]["totalCount"] == 50
    
    @pytest.mark.asyncio
    async def test_publish_bulk_operation_failed(self, dapr_publisher, mock_response):
        """Test bulk.failed event"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await dapr_publisher.publish_bulk_operation_failed(
                operation="update",
                error_message="Database connection failed",
                operation_id="bulk-456",
                executed_by="user123",
                correlation_id="corr-123"
            )
            
            assert result is True
            payload = mock_client.post.call_args[1]["json"]
            assert payload["type"] == "com.aioutlet.product.bulk.failed.v1"
            assert payload["data"]["errorMessage"] == "Database connection failed"
