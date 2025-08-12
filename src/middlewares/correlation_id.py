import uuid
from typing import Optional
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID
correlation_id_context: ContextVar[str] = ContextVar('correlation_id', default='')

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for distributed tracing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get('x-correlation-id', str(uuid.uuid4()))
        
        # Set correlation ID in context
        correlation_id_context.set(correlation_id)
        
        # Add correlation ID to request state for easy access
        request.state.correlation_id = correlation_id
        
        print(f"[{correlation_id}] {request.method} {request.url.path} - Processing request")
        
        # Process the request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response

def get_correlation_id() -> str:
    """
    Get the current correlation ID from context
    """
    return correlation_id_context.get('')

def create_headers_with_correlation_id(additional_headers: Optional[dict] = None) -> dict:
    """
    Create headers with correlation ID for outgoing requests
    """
    headers = {
        'X-Correlation-ID': get_correlation_id(),
        'Content-Type': 'application/json'
    }
    
    if additional_headers:
        headers.update(additional_headers)
    
    return headers
