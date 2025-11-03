"""
Unit tests for Dapr Publisher Service
Tests PRD REQ-3.x: Event Publishing requirements
"""
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.services.dapr_publisher import DaprPublisher, get_dapr_publisher


class TestDaprPublisher:
    """Test suite for DaprPublisher class"""

    @pytest.fixture
    def publisher(self):
        """Create a DaprPublisher instance for testing"""
        return DaprPublisher()

    @pytest.fixture
    def mock_dapr_client(self):
        """Mock DaprClient for testing"""
        with patch('src.services.dapr_publisher.DaprClient') as mock:
            client_instance = MagicMock()
            mock.return_value.__enter__ = Mock(return_value=client_instance)
            mock.return_value.__exit__ = Mock(return_value=None)
            yield client_instance

    @pytest.fixture
    def mock_logger(self):
        """Mock logger for testing"""
        with patch('src.services.dapr_publisher.logger') as mock:
            yield mock

    def test_publisher_initialization(self, publisher):
        """Test DaprPublisher initialization with default values"""
        assert publisher.dapr_http_port == '3500'
        assert publisher.dapr_grpc_port == '50001'
        assert publisher.pubsub_name == 'aioutlet-pubsub'
        assert publisher.service_name == 'product-service'

    def test_publisher_initialization_with_env_vars(self):
        """Test DaprPublisher initialization with environment variables"""
        with patch.dict('os.environ', {
            'DAPR_HTTP_PORT': '4500',
            'DAPR_GRPC_PORT': '51001',
            'SERVICE_NAME': 'test-service'
        }):
            publisher = DaprPublisher()
            assert publisher.dapr_http_port == '4500'
            assert publisher.dapr_grpc_port == '51001'
            assert publisher.service_name == 'test-service'

    @pytest.mark.asyncio
    async def test_publish_event_success(
        self,
        publisher,
        mock_dapr_client,
        mock_logger
    ):
        """Test successful event publishing via Dapr"""
        # Arrange
        event_type = 'product.created'
        data = {
            'productId': '123',
            'name': 'Test Product',
            'price': 99.99
        }
        correlation_id = 'test-correlation-123'

        # Act
        await publisher.publish(event_type, data, correlation_id)

        # Assert
        mock_dapr_client.publish_event.assert_called_once()
        call_args = mock_dapr_client.publish_event.call_args
        assert call_args[1]['pubsub_name'] == 'aioutlet-pubsub'
        assert call_args[1]['topic_name'] == event_type
        assert call_args[1]['data_content_type'] == 'application/json'

        # Verify event payload structure
        published_data = json.loads(call_args[1]['data'])
        assert published_data['eventType'] == event_type
        assert published_data['source'] == 'product-service'
        assert published_data['correlationId'] == correlation_id
        assert published_data['data'] == data
        assert 'eventId' in published_data
        assert 'timestamp' in published_data

        # Verify logger was called with success
        mock_logger.info.assert_called_once()
        assert 'Published event via Dapr' in mock_logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_publish_event_without_correlation_id(
        self,
        publisher,
        mock_dapr_client,
        mock_logger
    ):
        """Test event publishing without correlation ID"""
        # Arrange
        event_type = 'product.updated'
        data = {'productId': '456'}

        # Act
        await publisher.publish(event_type, data)

        # Assert
        mock_dapr_client.publish_event.assert_called_once()
        call_args = mock_dapr_client.publish_event.call_args
        published_data = json.loads(call_args[1]['data'])
        assert published_data['correlationId'] is None

    @pytest.mark.asyncio
    async def test_publish_event_failure_logged_not_raised(
        self,
        publisher,
        mock_dapr_client,
        mock_logger
    ):
        """Test that publishing failures are logged but not raised (fire-and-forget)"""
        # Arrange
        event_type = 'product.deleted'
        data = {'productId': '789'}
        correlation_id = 'test-correlation-456'
        mock_dapr_client.publish_event.side_effect = Exception('Connection failed')

        # Act - should not raise exception
        await publisher.publish(event_type, data, correlation_id)

        # Assert
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert 'Failed to publish event via Dapr' in error_msg
        assert 'Connection failed' in error_msg

        # Verify error metadata
        error_metadata = mock_logger.error.call_args[1]['metadata']
        assert error_metadata['correlationId'] == correlation_id
        assert error_metadata['eventType'] == event_type
        assert 'error' in error_metadata
        assert 'errorType' in error_metadata

    @pytest.mark.asyncio
    async def test_publish_multiple_events(
        self,
        publisher,
        mock_dapr_client,
        mock_logger
    ):
        """Test publishing multiple events"""
        # Arrange
        events = [
            ('product.created', {'productId': '1'}),
            ('product.updated', {'productId': '2'}),
            (
                'product.price.changed',
                {'productId': '3', 'oldPrice': 10, 'newPrice': 15}
            )
        ]

        # Act
        for event_type, data in events:
            await publisher.publish(event_type, data)

        # Assert
        assert mock_dapr_client.publish_event.call_count == 3
        assert mock_logger.info.call_count == 3

    @pytest.mark.asyncio
    async def test_event_payload_timestamp_format(
        self,
        publisher,
        mock_dapr_client
    ):
        """Test timestamp is in ISO 8601 format with UTC timezone"""
        # Act
        await publisher.publish('test.event', {'key': 'value'})

        # Assert
        call_args = mock_dapr_client.publish_event.call_args
        published_data = json.loads(call_args[1]['data'])
        timestamp = published_data['timestamp']

        # Verify ISO 8601 format
        parsed_time = datetime.fromisoformat(
            timestamp.replace('Z', '+00:00')
        )
        assert isinstance(parsed_time, datetime)

    @pytest.mark.asyncio
    async def test_event_id_uniqueness(
        self,
        publisher,
        mock_dapr_client
    ):
        """Test that each event gets a unique event ID"""
        # Act
        await publisher.publish('test.event', {'key': 'value1'})
        await publisher.publish('test.event', {'key': 'value2'})

        # Assert
        assert mock_dapr_client.publish_event.call_count == 2
        call1_data = json.loads(
            mock_dapr_client.publish_event.call_args_list[0][1]['data']
        )
        call2_data = json.loads(
            mock_dapr_client.publish_event.call_args_list[1][1]['data']
        )
        assert call1_data['eventId'] != call2_data['eventId']

    def test_get_dapr_publisher_singleton(self):
        """Test that get_dapr_publisher returns a singleton instance"""
        publisher1 = get_dapr_publisher()
        publisher2 = get_dapr_publisher()
        assert publisher1 is publisher2

    @pytest.mark.asyncio
    async def test_publish_with_complex_data(
        self,
        publisher,
        mock_dapr_client
    ):
        """Test publishing events with complex nested data structures"""
        # Arrange
        complex_data = {
            'productId': '123',
            'variations': [
                {'sku': 'SKU1', 'color': 'red', 'size': 'M'},
                {'sku': 'SKU2', 'color': 'blue', 'size': 'L'}
            ],
            'metadata': {
                'tags': ['sale', 'featured'],
                'attributes': {'material': 'cotton', 'brand': 'TestBrand'}
            }
        }

        # Act
        await publisher.publish('product.created', complex_data)

        # Assert
        call_args = mock_dapr_client.publish_event.call_args
        published_data = json.loads(call_args[1]['data'])
        assert published_data['data'] == complex_data

    @pytest.mark.asyncio
    async def test_publish_event_types_match_prd_requirements(
        self,
        publisher,
        mock_dapr_client
    ):
        """Test that event types match PRD REQ-3.1.x requirements"""
        # PRD required event types
        event_types = [
            'product.created',           # REQ-3.1.1
            'product.updated',           # REQ-3.1.2
            'product.deleted',           # REQ-3.1.3
            'product.price.changed',     # REQ-3.1.4
            'product.back.in.stock',     # REQ-3.1.5
            'product.badge.auto.assigned',  # REQ-3.1.6
            'product.badge.auto.removed',   # REQ-3.1.6
        ]

        # Act & Assert
        for event_type in event_types:
            await publisher.publish(event_type, {'test': 'data'})

        # Verify all events were published
        assert mock_dapr_client.publish_event.call_count == len(event_types)
