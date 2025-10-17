# Import tracing initialization first (before any other imports)
import sys
import os

# Add the parent directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables BEFORE any other imports that might need them
from dotenv import load_dotenv
load_dotenv()

import src.shared.tracing_init  # This must be first to ensure OpenTelemetry SDK is initialized

import logging

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.controllers import operational_controller
from src.api.controllers.product_controller import get_admin_stats
from src.shared.core.errors import (
    ErrorResponse,
    error_response_handler,
    http_exception_handler,
)
from src.shared.middlewares import CorrelationIdMiddleware
from src.shared.observability.logging import logger
from src.api.routers import home_router, product_router
from src.shared.db.mongodb import get_product_collection

# Import limiter from review_router since that's where rate limiting is used
from src.api.routers.review_router import limiter

app = FastAPI()

# Tracing already initialized in src.shared.tracing_init

# Add correlation ID middleware first
app.add_middleware(CorrelationIdMiddleware)

# Attach limiter to app state for SlowAPI compatibility
app.state.limiter = limiter

# Register centralized error handlers
app.add_exception_handler(ErrorResponse, error_response_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(
        f"Validation error: {exc.errors()}",
        metadata={"businessEvent": "VALIDATION_ERROR", "errors": exc.errors()}
    )
    return JSONResponse(
        status_code=422, content={"error": "Validation error", "details": exc.errors()}
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.security(
        logger.SecurityEvents.RATE_LIMIT_EXCEEDED,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"endpoint": str(request.url)}
    )
    return PlainTextResponse("Rate limit exceeded", status_code=429)


# Include routers
app.include_router(product_router, prefix="/api/products", tags=["products"])
app.include_router(home_router, prefix="/api/home", tags=["home"])

# Admin routes - register the admin stats endpoint directly
@app.get("/api/admin/stats")
async def admin_stats_endpoint(collection=Depends(get_product_collection)):
    """Get product statistics for admin dashboard"""
    return await get_admin_stats(collection)

# Operational endpoints for infrastructure/monitoring
app.get("/health")(operational_controller.health)
app.get("/health/ready")(operational_controller.readiness)
app.get("/health/live")(operational_controller.liveness)
app.get("/metrics")(operational_controller.metrics)

# Add SlowAPI middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    logger.info(f"Product API service starting on port {port}")
    
    # Log startup configuration
    logger.info(
        "Service configuration",
        metadata={
            "service": {
                "name": os.getenv("SERVICE_NAME", "product-service"),
                "version": os.getenv("SERVICE_VERSION", "1.0.0"),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "port": port
            },
            "tracing": {
                "enabled": os.getenv("ENABLE_TRACING", "true").lower() == "true",
                "endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            }
        }
    )
    
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)  # nosec B104
