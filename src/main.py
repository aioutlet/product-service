# Import tracing initialization first (before any other imports)
import sys
import os

# Add the parent directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Industry-standard initialization pattern:
# 1. Load environment variables
# 2. Validate configuration (blocking - must pass)
# 3. Initialize logger (uses validated config)
# 4. Check dependency health (non-blocking - log only)
# 5. Start application
# 
# Note: Distributed tracing is handled automatically by Dapr sidecar

# STEP 1: Load environment variables
from dotenv import load_dotenv
load_dotenv()

# STEP 2: Validate configuration (BLOCKING - must pass)
from src.validators import validate_config
validate_config()

# STEP 3: Initialize logger (after config validation)
from src.core.logger import logger

# STEP 4: Import application modules
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.errors import (
    ErrorResponse,
    error_response_handler,
    http_exception_handler,
)
from src.middleware import CorrelationIdMiddleware
from src.api import products_router, health_router, admin_router, variations_router, badges_router
from src.dependencies import get_products_collection

# STEP 5: Check dependency health (non-blocking)
async def check_dependencies_on_startup():
    """Check dependencies after application starts"""
    from src.utils import check_dependency_health, get_dependencies
    
    logger.info('Checking dependency health...')
    dependencies = get_dependencies()
    
    # Always check dependencies (includes MongoDB health check)
    try:
        await check_dependency_health(dependencies)
    except Exception as error:
        logger.warning(f'Dependency health check failed: {str(error)}')

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
    """Run dependency health checks and log startup info after FastAPI starts"""
    # Log startup configuration
    port = int(os.getenv("PORT", 8003))
    logger.info(f"Product API service starting on port {port}")
    logger.info(
        "Service configuration",
        metadata={
            "service": {
                "name": os.getenv("SERVICE_NAME", "product-service"),
                "version": os.getenv("SERVICE_VERSION", "1.0.0"),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "port": port
            }
        }
    )
    
    # Create database indexes
    from src.core.database import get_db
    from src.core.indexes import create_indexes
    db = await get_db()
    await create_indexes(db)
    
    # Check dependencies
    await check_dependencies_on_startup()


# Include routers
app.include_router(products_router, prefix="/api")
app.include_router(variations_router, prefix="/api")
app.include_router(badges_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)  # nosec B104
