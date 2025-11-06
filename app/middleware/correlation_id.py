"""
Correlation ID Middleware for request tracing
Ensures every request has a unique correlation ID for distributed tracing
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import config

# Context variable to store correlation ID for the current request
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get the correlation ID from the current context"""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the current context"""
    correlation_id_ctx.set(correlation_id)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for request tracing
    
    - Extracts correlation ID from request headers (or generates a new one)
    - Stores it in context for use throughout the request lifecycle
    - Adds it to response headers
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate a new one
        correlation_id = request.headers.get(
            config.correlation_id_header,
            str(uuid.uuid4())
        )
        
        # Store in context for access throughout the request
        set_correlation_id(correlation_id)
        
        # Add to request state for easy access
        request.state.correlation_id = correlation_id
        
        # Process the request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[config.correlation_id_header] = correlation_id
        
        return response
