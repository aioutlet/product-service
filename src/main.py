"""
Product Service - FastAPI application with Dapr integration
Clean, production-ready microservice with dependency health checking
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Add the parent directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables early
load_dotenv()

# Validate configuration (must pass before starting)
from src.validators.config_validator import validate_config
validate_config()

# Import application components
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

async def check_dependencies_on_startup():
    """Check dependencies after application starts - non-blocking health checks"""
    from src.utils.dependency_health_checker import check_dependency_health
    
    logger.info("Starting dependency health checks", metadata={"operation": "startup"})
    
    try:
        await check_dependency_health()
    except Exception as error:
        logger.warning(
            "Dependency health check failed",
            metadata={"operation": "startup", "error": str(error)}
        )


# Create FastAPI application
app = FastAPI(
    title="Product Service",
    description="Microservice for product management with Dapr integration",
    version=os.getenv("SERVICE_VERSION", "1.0.0")
)

# Configure middleware and error handlers
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(ErrorResponse, error_response_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.error(
        "Request validation error",
        metadata={"validation_errors": exc.errors()}
    )
    return JSONResponse(
        status_code=422, 
        content={"error": "Validation error", "details": exc.errors()}
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event - run health checks"""
    await check_dependencies_on_startup()


# Register API routes
app.include_router(product_router, prefix="/api/products", tags=["products"])
app.include_router(home_router, prefix="/api/home", tags=["home"])

# Admin endpoints
@app.get("/api/admin/stats", tags=["admin"])
async def admin_stats_endpoint(collection=Depends(get_product_collection)):
    """Get product statistics for admin dashboard"""
    return await get_admin_stats(collection)

# Health check endpoints for infrastructure
app.get("/health", tags=["health"])(operational_controller.health)
app.get("/health/ready", tags=["health"])(operational_controller.readiness)
app.get("/health/live", tags=["health"])(operational_controller.liveness)
app.get("/metrics", tags=["monitoring"])(operational_controller.metrics)

if __name__ == "__main__":
    """Development server entry point"""
    port = int(os.getenv("PORT", 8003))
    
    logger.info(
        "Starting Product Service",
        metadata={
            "service_name": os.getenv("SERVICE_NAME", "product-service"),
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "port": port
        }
    )
    
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True
    )  # nosec B104
