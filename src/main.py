# Import tracing initialization first (before any other imports)
import sys
import os

# Add the parent directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Industry-standard initialization pattern:
# 1. Load environment variables
# 2. Validate configuration (blocking - must pass)
# 3. Initialize tracing and observability
# 4. Check dependency health (non-blocking - log only)
# 5. Start application

# STEP 1: Load environment variables
print('Step 1: Loading environment variables...')
from dotenv import load_dotenv
load_dotenv()

# STEP 2: Validate configuration (BLOCKING - must pass)
print('Step 2: Validating configuration...')
from src.validators.config_validator import validate_config
validate_config()

# STEP 3: Initialize tracing (must be after config validation, before other imports)
print('Step 3: Initializing observability...')
import src.tracing_init  # This must be before other imports to ensure OpenTelemetry SDK is initialized

import logging
import asyncio
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.controllers import operational_controller
from src.controllers.product_controller import get_admin_stats
from src.core.errors import (
    ErrorResponse,
    error_response_handler,
    http_exception_handler,
)
from src.middlewares import CorrelationIdMiddleware
from src.observability.logging import logger
from src.routers import home_router, product_router
from src.routers.event_subscriptions import router as event_subscriptions_router
from src.routers.admin_router import router as admin_router
from src.routers.variation_router import router as variation_router
from src.db.mongodb import get_product_collection

# STEP 4: Check dependency health (non-blocking)
async def check_dependencies_on_startup():
    """Check dependencies after application starts"""
    from src.utils.dependency_health_checker import check_dependency_health, get_dependencies
    
    print('Step 4: Checking dependency health...')
    dependencies = get_dependencies()
    dependency_count = len(dependencies)

    if dependency_count > 0:
        print(f'[DEPS] Found {dependency_count} dependencies to check')
        try:
            await check_dependency_health(dependencies)
        except Exception as error:
            print(f'[DEPS] ⚠️ Dependency health check failed: {str(error)}')
    else:
        print('[DEPS] 📝 No dependencies configured for health checking')

app = FastAPI()

# Add correlation ID middleware first
app.add_middleware(CorrelationIdMiddleware)

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


@app.on_event("startup")
async def startup_event():
    """Run dependency health checks after FastAPI starts"""
    await check_dependencies_on_startup()


# Include routers
app.include_router(product_router, prefix="/api/products", tags=["products"])
app.include_router(home_router, prefix="/api/home", tags=["home"])
app.include_router(event_subscriptions_router, tags=["events"])  # Event consumption (REQ-3.2)
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])  # Admin features (REQ-5.x)
app.include_router(variation_router, prefix="/api/variations", tags=["variations"])  # Product variations (REQ-7/8.1-8.5)

# Legacy admin stats endpoint (kept for backward compatibility)
@app.get("/api/admin/stats-legacy")
async def admin_stats_endpoint(collection=Depends(get_product_collection)):
    """Get product statistics for admin dashboard"""
    return await get_admin_stats(collection)

# Operational endpoints for infrastructure/monitoring
app.get("/health")(operational_controller.health)
app.get("/health/ready")(operational_controller.readiness)
app.get("/health/live")(operational_controller.liveness)
app.get("/metrics")(operational_controller.metrics)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    
    print('Step 5: Starting product service...')
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
    
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)  # nosec B104
