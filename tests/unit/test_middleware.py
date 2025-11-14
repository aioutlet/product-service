"""Unit tests for middleware components"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request

from app.middleware.correlation_id import CorrelationIdMiddleware, get_correlation_id, set_correlation_id


class TestCorrelationIdMiddleware:
    """Test CorrelationIdMiddleware functionality"""

    @pytest.mark.asyncio
    @patch('app.middleware.correlation_id.config')
    async def test_correlation_id_from_header(self, mock_config):
        """Test extracting correlation ID from request header"""
        # Arrange
        mock_config.correlation_id_header = "X-Correlation-ID"
        
        app = Mock()
        middleware = CorrelationIdMiddleware(app)
        
        class MockRequest:
            def __init__(self):
                self.headers = {"X-Correlation-ID": "test-correlation-123"}
                self.state = Mock()
        
        request = MockRequest()
        
        captured_id = None
        
        async def call_next(req):
            # Capture the correlation ID that was set
            nonlocal captured_id
            captured_id = get_correlation_id()
            response = Mock()
            response.headers = {}
            return response
        
        # Act
        response = await middleware.dispatch(request, call_next)

        # Assert
        assert captured_id == "test-correlation-123"
        assert response.headers["X-Correlation-ID"] == "test-correlation-123"

    @pytest.mark.asyncio
    @patch('app.middleware.correlation_id.config')
    async def test_correlation_id_generated(self, mock_config):
        """Test generating new correlation ID when not provided"""
        # Arrange
        mock_config.correlation_id_header = "X-Correlation-ID"
        
        app = Mock()
        middleware = CorrelationIdMiddleware(app)
        
        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.state = Mock()
        
        request = MockRequest()
        
        generated_id = None
        
        async def call_next(req):
            nonlocal generated_id
            generated_id = get_correlation_id()
            response = Mock()
            response.headers = {}
            return response
        
        # Act
        response = await middleware.dispatch(request, call_next)

        # Assert
        assert generated_id is not None
        assert len(generated_id) > 0
        assert response.headers["X-Correlation-ID"] == generated_id
        # Verify it's a valid UUID format
        import uuid
        assert uuid.UUID(generated_id)

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID"""
        # Arrange
        test_id = "test-correlation-456"
        
        # Act
        set_correlation_id(test_id)
        result = get_correlation_id()

        # Assert
        assert result == test_id

    def test_get_correlation_id_none(self):
        """Test getting correlation ID returns None when not set"""
        # The context variable is per-context, so we need to reset it
        set_correlation_id(None)
        
        # Act
        result = get_correlation_id()

        # Assert
        assert result is None

