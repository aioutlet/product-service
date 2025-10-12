"""
Observability middleware for FastAPI
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..middlewares.correlation_id import get_correlation_id
from .logger import logger
from .tracing import add_span_attributes, create_span_context


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add observability features to FastAPI requests
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get correlation ID from existing middleware
        correlation_id = get_correlation_id()
        
        # Start timing
        start_time = time.time()
        
        # Extract request details
        method = request.method
        url_path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        client_ip = self._get_client_ip(request)
        
        # Create span for the request
        span_name = f"{method} {url_path}"
        with create_span_context(span_name, {
            "http.method": method,
            "http.url": str(request.url),
            "http.route": url_path,
            "http.user_agent": user_agent,
            "http.client_ip": client_ip,
            "correlation.id": correlation_id
        }) as span:
            
            # Log request start
            logger.debug(
                f"Request started: {method} {url_path}",
                correlation_id=correlation_id,
                metadata={
                    "request": {
                        "method": method,
                        "path": url_path,
                        "userAgent": user_agent,
                        "clientIp": client_ip
                    }
                }
            )
            
            # Process request
            try:
                response = await call_next(request)
                
                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Add response attributes to span
                add_span_attributes({
                    "http.status_code": response.status_code,
                    "http.response.duration_ms": duration_ms
                })
                
                # Log request completion
                level = "warning" if response.status_code >= 400 else "info"
                getattr(logger, level)(
                    f"Request completed: {method} {url_path} - {response.status_code}",
                    correlation_id=correlation_id,
                    metadata={
                        "request": {
                            "method": method,
                            "path": url_path,
                            "userAgent": user_agent,
                            "clientIp": client_ip
                        },
                        "response": {
                            "statusCode": response.status_code,
                            "durationMs": duration_ms
                        }
                    }
                )
                
                # Log performance if slow
                if duration_ms > 1000:  # Log if request takes more than 1 second
                    logger.performance(
                        f"Slow request: {method} {url_path}",
                        duration_ms=duration_ms,
                        threshold_ms=1000,
                        metadata={
                            "request": {
                                "method": method,
                                "path": url_path
                            }
                        }
                    )
                
                return response
                
            except Exception as e:
                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Environment-based error logging
                is_development = os.getenv('ENVIRONMENT', 'development') == 'development'
                
                # Add error attributes to span
                add_span_attributes({
                    "error": True,
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                    "http.response.duration_ms": duration_ms
                })
                
                # Log request failure with environment-specific stack trace handling
                if is_development:
                    import traceback
                    logger.error(
                        f"Request failed: {method} {url_path}",
                        correlation_id=correlation_id,
                        error=e,
                        metadata={
                            "request": {
                                "method": method,
                                "path": url_path,
                                "userAgent": user_agent,
                                "clientIp": client_ip
                            },
                            "response": {
                                "durationMs": duration_ms
                            },
                            "traceback": traceback.format_exc()
                        }
                    )
                else:
                    logger.error(
                        f"Request failed: {method} {url_path}",
                        correlation_id=correlation_id,
                        error=str(e),
                        metadata={
                            "request": {
                                "method": method,
                                "path": url_path,
                                "userAgent": user_agent,
                                "clientIp": client_ip
                            },
                            "response": {
                                "durationMs": duration_ms
                            },
                            "environment": os.getenv('ENVIRONMENT', 'development')
                        }
                    )
                
                # Re-raise the exception
                raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        """
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        client_host = request.client.host if request.client else "unknown"
        return client_host
