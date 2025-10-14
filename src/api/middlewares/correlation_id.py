from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.utils.correlation_id import (
    set_correlation_id,
    extract_correlation_id_from_headers,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for distributed tracing
    """

    async def dispatch(self, request: Request, call_next):
        # Extract correlation ID from headers or generate new one
        correlation_id = extract_correlation_id_from_headers(dict(request.headers))

        # Set correlation ID in context (shared across API and Consumer)
        set_correlation_id(correlation_id)

        # Add correlation ID to request state for easy access
        request.state.correlation_id = correlation_id

        # Import logger here to avoid circular imports
        try:
            from src.shared.observability.logging import logger
            logger.debug(
                f"{request.method} {request.url.path} - Processing request",
                correlation_id=correlation_id,
                metadata={
                    "request": {
                        "method": request.method,
                        "path": request.url.path,
                        "correlationId": correlation_id
                    }
                }
            )
        except ImportError:
            # Fallback to print if observability not available
            print(
                f"[{correlation_id}] {request.method} {request.url.path} - "
                "Processing request"
            )

        # Process the request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


# Note: get_correlation_id and create_headers_with_correlation_id
# are now available from src.shared.utils.correlation_id
# Import them from there if needed in other modules
