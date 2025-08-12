import os
import logging
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from src.routers import product_router, home_router
from src.controllers import operational_controller
from src.routers.review_router import limiter  # Import limiter from review_router since that's where rate limiting is used
from src.core.errors import error_response_handler, http_exception_handler, ErrorResponse
from src.core.logger import logger
from src.middlewares.correlation_id import CorrelationIdMiddleware

# Load environment variables once at the entrypoint
load_dotenv()

app = FastAPI()

# Add correlation ID middleware first
app.add_middleware(CorrelationIdMiddleware)

# Attach limiter to app state for SlowAPI compatibility
app.state.limiter = limiter

# Register centralized error handlers
app.add_exception_handler(ErrorResponse, error_response_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}", extra={"event": "validation_error"})
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()}
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return PlainTextResponse("Rate limit exceeded", status_code=429)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Include routers
app.include_router(product_router, prefix="/api/products", tags=["products"])
app.include_router(home_router, prefix="/api/home", tags=["home"])

# Operational endpoints for infrastructure/monitoring
app.get("/health")(operational_controller.health)
app.get("/health/ready")(operational_controller.readiness)
app.get("/health/live")(operational_controller.liveness)
app.get("/metrics")(operational_controller.metrics)

# Add SlowAPI middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Product service running on port {port}")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
