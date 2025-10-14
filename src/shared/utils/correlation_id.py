"""
Correlation ID utilities for distributed tracing
Shared across API and Consumer components
"""

import uuid
from contextvars import ContextVar
from typing import Optional, Dict

# Context variable to store correlation ID across async operations
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """
    Get the current correlation ID from context
    Generates a new one if none exists
    
    Returns:
        str: Current correlation ID
    """
    correlation_id = correlation_id_context.get("")
    if not correlation_id:
        # Generate a new correlation ID if none exists in context
        correlation_id = str(uuid.uuid4())
        correlation_id_context.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in context
    
    Args:
        correlation_id: The correlation ID to set
    """
    correlation_id_context.set(correlation_id)


def create_correlation_id() -> str:
    """
    Create a new correlation ID
    
    Returns:
        str: New UUID-based correlation ID
    """
    return str(uuid.uuid4())


def create_headers_with_correlation_id(
    additional_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Create headers with correlation ID for outgoing requests
    Useful for maintaining tracing across service calls
    
    Args:
        additional_headers: Optional additional headers to include
        
    Returns:
        dict: Headers dictionary with correlation ID
    """
    headers = {
        "X-Correlation-ID": get_correlation_id(),
        "Content-Type": "application/json",
    }

    if additional_headers:
        headers.update(additional_headers)

    return headers


def extract_correlation_id_from_headers(headers: Dict[str, str]) -> str:
    """
    Extract correlation ID from request headers
    Generates new one if not present
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        str: Correlation ID from headers or newly generated
    """
    # Try different header variations (case-insensitive)
    correlation_id = (
        headers.get("x-correlation-id")
        or headers.get("X-Correlation-ID")
        or headers.get("X-CORRELATION-ID")
    )
    
    if not correlation_id:
        correlation_id = create_correlation_id()
    
    return correlation_id
