from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.correlation_id import (
    extract_correlation_id_from_headers,
    set_correlation_id,
    create_correlation_id,
    CORRELATION_ID_HEADER,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract or generate correlation IDs for requests.
    Sets the correlation ID in the context for use throughout the request lifecycle.
    """

    async def dispatch(self, request, call_next):
        # Extract correlation ID from headers or generate a new one
        correlation_id = extract_correlation_id_from_headers(
            dict(request.headers)
        ) or create_correlation_id()

        # Set in context
        set_correlation_id(correlation_id)

        # Process the request
        response = await call_next(request)

        # Add correlation ID to response headers using configured header name
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response
