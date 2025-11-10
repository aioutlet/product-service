"""
FastAPI Application - Product Service
Following FastAPI best practices with proper separation of concerns
"""

# Load environment variables from .env file FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import config
from app.core.errors import error_response_handler, http_exception_handler, ErrorResponse
from app.core.logger import logger
from app.core.telemetry import init_telemetry, instrument_app
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api import products, health, operational, admin, home, events
from app.middleware import TraceContextMiddleware

# Initialize OpenTelemetry tracing BEFORE creating FastAPI app
init_telemetry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Product Service...")
    await connect_to_mongo()
    
    logger.info(
        "Product Service started successfully",
        metadata={
            "service_name": config.service_name,
            "version": config.service_version,
            "environment": config.environment,
            "port": config.port
        }
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Product Service...")
    await close_mongo_connection()


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Product Service",
    description="Microservice for product management with clean architecture",
    version=config.service_version,
    lifespan=lifespan
)

# Instrument app with OpenTelemetry for automatic tracing
instrument_app(app)

# Configure error handlers
app.add_exception_handler(ErrorResponse, error_response_handler)
app.add_exception_handler(RequestValidationError, lambda request, exc: JSONResponse(
    status_code=422,
    content={"error": "Validation error", "details": exc.errors()}
))

# Add W3C Trace Context middleware
app.add_middleware(TraceContextMiddleware)

# Include API routers
app.include_router(home.router, tags=["home"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(operational.router, prefix="/api", tags=["operational"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(events.router)  # Dapr pub/sub event subscriptions


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        f"Starting {config.service_name} on port {config.port}",
        metadata={
            "service_name": config.service_name,
            "version": config.service_version,
            "environment": config.environment,
            "port": config.port
        }
    )
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.environment == "development"
    )