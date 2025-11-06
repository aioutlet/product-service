# Import tracing initialization first (before any other imports)
import sys
import os

# Add the parent directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Industry-standard initialization pattern:
# 1. Load environment variables
# 2. Validate configuration (blocking - must pass)
# 3. Initialize observability (handled by Dapr)
# 4. Check dependency health (non-blocking - log only)
# 5. Start application

# STEP 1: Load environment variables
from dotenv import load_dotenv
load_dotenv()

# STEP 2: Validate configuration (BLOCKING - must pass)
from src.validators.config_validator import validate_config
validate_config()

# STEP 3: Initialize observability (must be after config validation, before other imports)
    # Observability is now handled by Dapr automatically


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
from src.core.logger import logger
from src.routers import home_router, product_router
from src.db.mongodb import get_product_collection

# STEP 4: Check dependency health (non-blocking)
async def check_dependencies_on_startup():
    """Check dependencies after application starts"""
    from src.utils.dependency_health_checker import check_dependency_health, get_dependencies
    
    logger.info("Starting dependency health checks", metadata={"operation": "startup"})
    dependencies = get_dependencies()
    dependency_count = len(dependencies)

    if dependency_count > 0:
        logger.info(
            "Found dependencies to check",
            metadata={
                "operation": "startup",
                "dependency_count": dependency_count
            }
        )
        try:
            await check_dependency_health(dependencies)
        except Exception as error:
            logger.warning(
                "Dependency health check failed",
                metadata={
                    "operation": "startup",
                    "error": str(error)
                }
            )
    else:
        logger.info(
            "No dependencies configured for health checking",
            metadata={"operation": "startup"}
        )

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
    """Run dependency health checks and test database connection after FastAPI starts"""
    await check_dependencies_on_startup()


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
