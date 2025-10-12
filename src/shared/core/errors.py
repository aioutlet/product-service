# Error handling utilities

import os
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.shared.core.logger import logger

# Environment detection
IS_DEVELOPMENT = os.getenv('ENVIRONMENT', 'development') == 'development'
IS_PRODUCTION = os.getenv('ENVIRONMENT', 'development') == 'production'


class ErrorResponse(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def error_response_handler(request: Request, exc: ErrorResponse):
    # Log with environment-specific error details
    extra_data = {
        "event": "error_response",
        "status_code": exc.status_code,
        "url": str(request.url),
        "method": request.method,
        **exc.details,
    }
    
    if IS_DEVELOPMENT:
        # Include more detailed error info in development
        import traceback
        extra_data["traceback"] = traceback.format_exc()
    
    logger.error(
        f"Error: {exc.message}",
        extra=extra_data,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


def http_exception_handler(request: Request, exc: HTTPException):
    # Log with environment-specific error details
    extra_data = {
        "event": "http_exception", 
        "status_code": exc.status_code,
        "url": str(request.url),
        "method": request.method,
    }
    
    if IS_DEVELOPMENT:
        # Include more detailed error info in development
        import traceback
        extra_data["traceback"] = traceback.format_exc()
    
    logger.error(
        f"HTTPException: {exc.detail}",
        extra=extra_data,
    )
    
    return JSONResponse(
        status_code=exc.status_code, 
        content={"error": exc.detail}
    )


class ErrorResponseModel(BaseModel):
    error: str
    details: dict = None
