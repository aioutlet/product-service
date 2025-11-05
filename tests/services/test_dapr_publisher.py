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
