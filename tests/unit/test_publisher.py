"""Unit tests for Dapr event publisher"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.events.publishers.publisher import DaprEventPublisher


class TestDaprEventPublisher:
    """Test DaprEventPublisher for publishing events"""

    def setup_method(self):
        """Set up test fixtures"""
        self.publisher = DaprEventPublisher()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_event_success(self, mock_dapr_client):
        """Test successful event publishing"""
        # Arrange
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
        event_type = "product.created"
        data = {"productId": "123", "name": "Test Product"}
        correlation_id = "corr-123"

        # Act
        result = await self.publisher.publish_event(event_type, data, correlation_id)

        # Assert
        assert result is True
        mock_client_instance.publish_event.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_client_instance.publish_event.call_args
        assert call_args.kwargs['pubsub_name'] == "product-pubsub"
        assert call_args.kwargs['topic_name'] == event_type
        assert call_args.kwargs['data_content_type'] == "application/json"

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', False)
    async def test_publish_event_dapr_not_available(self):
        """Test publishing when Dapr is not available"""
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
    async def test_publish_event_exception(self, mock_dapr_client):
        """Test publishing event with exception"""
        # Arrange
        mock_client_instance = MagicMock()
        mock_client_instance.publish_event.side_effect = Exception("Connection error")
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
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
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
        product_id = "123"
        product_data = {"name": "Test Product", "price": 29.99}
        created_by = "user123"
        correlation_id = "corr-123"

        # Act
        result = await self.publisher.publish_product_created(
            product_id, product_data, created_by, correlation_id
        )

        # Assert
        assert result is True
        mock_client_instance.publish_event.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_product_updated(self, mock_dapr_client):
        """Test publishing product.updated event"""
        # Arrange
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
        product_id = "123"
        product_data = {"name": "Updated Product", "price": 39.99}
        updated_by = "admin"
        correlation_id = "corr-123"

        # Act
        result = await self.publisher.publish_product_updated(
            product_id, product_data, updated_by, correlation_id
        )

        # Assert
        assert result is True
        mock_client_instance.publish_event.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_product_deleted(self, mock_dapr_client):
        """Test publishing product.deleted event"""
        # Arrange
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
        product_id = "123"
        deleted_by = "admin"
        correlation_id = "corr-123"

        # Act
        result = await self.publisher.publish_product_deleted(
            product_id, deleted_by, correlation_id
        )

        # Assert
        assert result is True
        mock_client_instance.publish_event.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    @patch('app.events.publishers.publisher.get_trace_id')
    async def test_publish_event_uses_trace_id(self, mock_get_trace_id, mock_dapr_client):
        """Test that publish_event uses trace_id when correlation_id not provided"""
        # Arrange
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        mock_get_trace_id.return_value = "trace-123"
        
        event_type = "product.created"
        data = {"productId": "123"}

        # Act
        result = await self.publisher.publish_event(event_type, data)

        # Assert
        assert result is True
        mock_get_trace_id.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_event_payload_structure(self, mock_dapr_client):
        """Test that event payload has correct CloudEvents structure"""
        # Arrange
        import json
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
        event_type = "product.created"
        data = {"productId": "123", "name": "Test"}
        correlation_id = "corr-123"

        # Act
        await self.publisher.publish_event(event_type, data, correlation_id)

        # Assert
        call_args = mock_client_instance.publish_event.call_args
        event_data = call_args.kwargs['data']
        event_payload = json.loads(event_data)
        
        # Verify CloudEvents structure
        assert event_payload['specversion'] == "1.0"
        assert event_payload['type'] == event_type
        assert event_payload['source'] == self.publisher.service_name
        assert 'id' in event_payload
        assert 'time' in event_payload
        assert event_payload['datacontenttype'] == "application/json"
        assert event_payload['data'] == data
        assert event_payload['correlationId'] == correlation_id

    @pytest.mark.asyncio
    @patch('app.events.publishers.publisher.DAPR_AVAILABLE', True)
    @patch('app.events.publishers.publisher.DaprClient')
    async def test_publish_event_without_correlation_id(self, mock_dapr_client):
        """Test publishing event without explicit correlation_id"""
        # Arrange
        mock_client_instance = MagicMock()
        mock_dapr_client.return_value.__enter__.return_value = mock_client_instance
        
        event_type = "product.created"
        data = {"productId": "123"}

        # Act
        result = await self.publisher.publish_event(event_type, data)

        # Assert
        assert result is True
        mock_client_instance.publish_event.assert_called_once()
