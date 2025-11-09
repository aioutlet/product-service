"""Unit tests for event publisher"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.events.publishers.publisher import DaprEventPublisher


class TestDaprEventPublisher:
    """Test DaprEventPublisher functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.publisher = DaprEventPublisher()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_event_success(self, mock_dapr_client):
        """Test successful event publishing"""
        # Arrange
        mock_client = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client
        
        event_type = "product.created"
        data = {"productId": "123", "name": "Test Product"}
        correlation_id = "test-correlation-id"

        # Act
        result = await self.publisher.publish_event(event_type, data, correlation_id)

        # Assert
        assert result is True
        mock_client.publish_event.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_client.publish_event.call_args
        assert call_args.kwargs["pubsub_name"] == "product-pubsub"
        assert call_args.kwargs["topic_name"] == event_type
        assert call_args.kwargs["data_content_type"] == "application/json"

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', False)
    async def test_publish_event_dapr_not_available(self):
        """Test event publishing when Dapr is not available"""
        # Arrange
        event_type = "product.created"
        data = {"productId": "123"}
        
        # Act
        result = await self.publisher.publish_event(event_type, data)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_event_error_handling(self, mock_dapr_client):
        """Test error handling in event publishing"""
        # Arrange
        mock_client = MagicMock()
        mock_client.publish_event.side_effect = Exception("Connection error")
        mock_dapr_client.return_value.__enter__.return_value = mock_client
        
        event_type = "product.created"
        data = {"productId": "123"}

        # Act
        result = await self.publisher.publish_event(event_type, data)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_product_created(self, mock_dapr_client):
        """Test publishing product.created event"""
        # Arrange
        mock_client = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client
        
        product_id = "123"
        product_data = {"name": "Test Product", "price": 29.99}
        created_by = "user123"
        correlation_id = "test-correlation-id"

        # Act
        result = await self.publisher.publish_product_created(
            product_id, product_data, created_by, correlation_id
        )

        # Assert
        assert result is True
        mock_client.publish_event.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_product_updated(self, mock_dapr_client):
        """Test publishing product.updated event"""
        # Arrange
        mock_client = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client
        
        product_id = "123"
        product_data = {"name": "Updated Product", "price": 39.99}
        updated_by = "admin123"
        correlation_id = "test-correlation-id"

        # Act
        result = await self.publisher.publish_product_updated(
            product_id, product_data, updated_by, correlation_id
        )

        # Assert
        assert result is True
        mock_client.publish_event.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_product_deleted(self, mock_dapr_client):
        """Test publishing product.deleted event"""
        # Arrange
        mock_client = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client
        
        product_id = "123"
        deleted_by = "admin123"
        correlation_id = "test-correlation-id"

        # Act
        result = await self.publisher.publish_product_deleted(
            product_id, deleted_by, correlation_id
        )

        # Assert
        assert result is True
        mock_client.publish_event.assert_called_once()

    def test_publisher_initialization(self):
        """Test DaprEventPublisher initialization"""
        publisher = DaprEventPublisher()
        assert publisher.pubsub_name == "product-pubsub"
        assert publisher.service_name is not None
