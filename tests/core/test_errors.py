"""Tests for error handling"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.core.errors import ErrorResponse, error_response_handler, http_exception_handler


class TestErrorResponse:
    """Test ErrorResponse exception class"""

    def test_error_response_creation(self):
        """Test creating an ErrorResponse"""
        error = ErrorResponse("Something went wrong", status_code=400)
        assert error.message == "Something went wrong"
        assert error.status_code == 400
        assert error.details == {}

    def test_error_response_with_details(self):
        """Test creating an ErrorResponse with details"""
        details = {"field": "user_id", "issue": "required"}
        error = ErrorResponse("Validation failed", status_code=422, details=details)
        assert error.message == "Validation failed"
        assert error.status_code == 422
        assert error.details == details

    def test_error_response_default_status_code(self):
        """Test that ErrorResponse defaults to status code 400"""
        error = ErrorResponse("Bad request")
        assert error.status_code == 400

    def test_error_response_str(self):
        """Test string representation of ErrorResponse"""
        error = ErrorResponse("Test error")
        assert str(error) == "Test error"


class TestErrorHandlers:
    """Test error handler functions"""

    def test_error_response_handler(self):
        """Test error_response_handler function"""
        # Mock request object
        mock_request = Mock()
        
        # Create error
        error = ErrorResponse("Test error", status_code=404, details={"id": "123"})
        
        # Call handler with mocked logger
        with patch('src.core.errors.logger') as mock_logger:
            response = error_response_handler(mock_request, error)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # Check response content
        content = response.body.decode()
        assert "Test error" in content
        assert "123" in content

    def test_error_response_handler_no_details(self):
        """Test error_response_handler with no details"""
        mock_request = Mock()
        error = ErrorResponse("Simple error", status_code=500)
        
        with patch('src.core.errors.logger') as mock_logger:
            response = error_response_handler(mock_request, error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    def test_http_exception_handler(self):
        """Test http_exception_handler function"""
        # Mock request object
        mock_request = Mock()
        
        # Create HTTPException
        exception = HTTPException(status_code=403, detail="Forbidden")
        
        # Call handler with mocked logger
        with patch('src.core.errors.logger') as mock_logger:
            response = http_exception_handler(mock_request, exception)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        
        # Check response content
        content = response.body.decode()
        assert "Forbidden" in content

    def test_error_response_inheritance(self):
        """Test that ErrorResponse properly inherits from Exception"""
        error = ErrorResponse("Test error")
        assert isinstance(error, Exception)
        
        # Should be raisable
        with pytest.raises(ErrorResponse) as exc_info:
            raise error
        assert exc_info.value.message == "Test error"

    def test_multiple_error_details(self):
        """Test ErrorResponse with multiple detail fields"""
        details = {
            "product_id": "missing",
            "user_id": "invalid",
            "rating": "out_of_range"
        }
        error = ErrorResponse("Multiple validation errors", status_code=422, details=details)
        
        assert error.details["product_id"] == "missing"
        assert error.details["user_id"] == "invalid"
        assert error.details["rating"] == "out_of_range"