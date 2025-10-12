import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for distributed tracing
    """

    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))

        # Set correlation ID in context
        correlation_id_context.set(correlation_id)

        # Add correlation ID to request state for easy access
        request.state.correlation_id = correlation_id

        # Import logger here to avoid circular imports
        try:
            from src.shared.observability.logger import logger
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


def get_correlation_id() -> str:
    """
    Get the current correlation ID from context, generate one if none exists
    """
    correlation_id = correlation_id_context.get("")
    if not correlation_id:
        # Generate a new correlation ID if none exists in context
        correlation_id = str(uuid.uuid4())
        correlation_id_context.set(correlation_id)
    return correlation_id


def create_headers_with_correlation_id(
    additional_headers: Optional[dict] = None,
) -> dict:
    """
    Create headers with correlation ID for outgoing requests
    """
    headers = {
        "X-Correlation-ID": get_correlation_id(),
        "Content-Type": "application/json",
    }

    if additional_headers:
        headers.update(additional_headers)

    return headers
