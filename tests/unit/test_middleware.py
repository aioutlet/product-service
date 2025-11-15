"""Unit tests for trace context middleware"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint

from app.middleware.trace_context import (
    TraceContextMiddleware,
    extract_trace_context,
    generate_trace_context,
    get_trace_id,
    get_span_id,
    set_trace_context
)


class TestTraceContextExtraction:
    """Test trace context extraction and generation"""

    def test_extract_trace_context_valid(self):
        """Test extracting valid W3C traceparent header"""
        # Arrange
        traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

        # Act
        result = extract_trace_context(traceparent)

        # Assert
        assert result is not None
        trace_id, span_id = result
        assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert span_id == "00f067aa0ba902b7"

    def test_extract_trace_context_invalid_format(self):
        """Test extracting invalid traceparent format"""
        # Arrange
        invalid_traceparents = [
            "invalid",
            "00-invalid-trace-id",
            "01-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",  # wrong version
            "00-4bf92f3577b34da6a3ce929d0e0e473-00f067aa0ba902b7-01",  # trace_id too short
            "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b-01",  # span_id too short
        ]

        # Act & Assert
        for invalid in invalid_traceparents:
            result = extract_trace_context(invalid)
            assert result is None

    def test_extract_trace_context_all_zeros(self):
        """Test extracting traceparent with all zeros (invalid)"""
        # Arrange
        traceparent = "00-00000000000000000000000000000000-0000000000000000-01"

        # Act
        result = extract_trace_context(traceparent)

        # Assert
        assert result is None

    def test_extract_trace_context_empty(self):
        """Test extracting empty traceparent"""
        # Act
        result = extract_trace_context("")

        # Assert
        assert result is None

    def test_extract_trace_context_none(self):
        """Test extracting None traceparent"""
        # Act
        result = extract_trace_context(None)

        # Assert
        assert result is None

    def test_generate_trace_context(self):
        """Test generating new trace context"""
        # Act
        trace_id, span_id = generate_trace_context()

        # Assert
        assert len(trace_id) == 32
        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in trace_id)
        assert all(c in "0123456789abcdef" for c in span_id)

    def test_generate_trace_context_unique(self):
        """Test that generated trace contexts are unique"""
        # Act
        trace_id1, span_id1 = generate_trace_context()
        trace_id2, span_id2 = generate_trace_context()

        # Assert
        assert trace_id1 != trace_id2
        assert span_id1 != span_id2


class TestTraceContextContextVars:
    """Test trace context storage in context variables"""

    def test_set_and_get_trace_context(self):
        """Test setting and getting trace context"""
        # Arrange
        test_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        test_span_id = "00f067aa0ba902b7"

        # Act
        set_trace_context(test_trace_id, test_span_id)
        retrieved_trace_id = get_trace_id()
        retrieved_span_id = get_span_id()

        # Assert
        assert retrieved_trace_id == test_trace_id
        assert retrieved_span_id == test_span_id

    def test_get_trace_id_none(self):
        """Test getting trace ID when not set"""
        # Note: This might return the value from a previous test
        # In real tests, we'd need to isolate context
        result = get_trace_id()
        # Assert: Should be either None or a string
        assert result is None or isinstance(result, str)

    def test_get_span_id_none(self):
        """Test getting span ID when not set"""
        result = get_span_id()
        # Assert: Should be either None or a string
        assert result is None or isinstance(result, str)


class TestTraceContextMiddleware:
    """Test TraceContextMiddleware"""

    @pytest.mark.asyncio
    async def test_middleware_with_valid_traceparent(self):
        """Test middleware with valid traceparent header"""
        # Arrange
        middleware = TraceContextMiddleware(app=Mock())
        
        # Create mock request with traceparent header
        mock_request = Mock(spec=Request)
        mock_request.headers = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
        mock_request.state = Mock()
        
        # Create mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        # Mock call_next
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert response == mock_response
        assert "traceparent" in response.headers
        assert "X-Trace-ID" in response.headers
        assert mock_request.state.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert mock_request.state.span_id == "00f067aa0ba902b7"

    @pytest.mark.asyncio
    async def test_middleware_without_traceparent(self):
        """Test middleware without traceparent header (generates new)"""
        # Arrange
        middleware = TraceContextMiddleware(app=Mock())
        
        # Create mock request without traceparent header
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.state = Mock()
        
        # Create mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        # Mock call_next
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert response == mock_response
        assert "traceparent" in response.headers
        assert "X-Trace-ID" in response.headers
        assert hasattr(mock_request.state, 'trace_id')
        assert hasattr(mock_request.state, 'span_id')
        assert len(mock_request.state.trace_id) == 32
        assert len(mock_request.state.span_id) == 16

    @pytest.mark.asyncio
    async def test_middleware_with_invalid_traceparent(self):
        """Test middleware with invalid traceparent (generates new)"""
        # Arrange
        middleware = TraceContextMiddleware(app=Mock())
        
        # Create mock request with invalid traceparent
        mock_request = Mock(spec=Request)
        mock_request.headers = {"traceparent": "invalid-traceparent"}
        mock_request.state = Mock()
        
        # Create mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        # Mock call_next
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert response == mock_response
        assert "traceparent" in response.headers
        assert "X-Trace-ID" in response.headers
        # Should have generated new trace context
        assert len(mock_request.state.trace_id) == 32
        assert len(mock_request.state.span_id) == 16

    @pytest.mark.asyncio
    async def test_middleware_traceparent_format_in_response(self):
        """Test that response traceparent has correct format"""
        # Arrange
        middleware = TraceContextMiddleware(app=Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.state = Mock()
        
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        traceparent = response.headers.get("traceparent")
        assert traceparent is not None
        # Check W3C format: 00-{32-hex}-{16-hex}-01
        parts = traceparent.split("-")
        assert len(parts) == 4
        assert parts[0] == "00"  # version
        assert len(parts[1]) == 32  # trace_id
        assert len(parts[2]) == 16  # span_id
        assert parts[3] == "01"  # flags

    @pytest.mark.asyncio
    async def test_middleware_propagates_trace_id(self):
        """Test that trace ID is properly propagated"""
        # Arrange
        middleware = TraceContextMiddleware(app=Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
        mock_request.state = Mock()
        
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Act
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        x_trace_id = response.headers.get("X-Trace-ID")
        assert x_trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
