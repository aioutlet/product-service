"""
Error handling utilities following FastAPI best practices
"""

import traceback
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import config
from app.core.logger import logger


class ErrorResponse(Exception):
    """Custom exception for application errors"""
    
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ErrorResponseModel(BaseModel):
    """Pydantic model for error responses"""
    error: str
    details: dict = None


async def error_response_handler(request: Request, exc: ErrorResponse):
    """Handler for custom ErrorResponse exceptions"""
    metadata = {
        "event": "error_response",
        "status_code": exc.status_code,
        "url": str(request.url),
        "method": request.method,
        **exc.details,
    }
    
    if config.environment == "development":
        # Include more detailed error info in development
        metadata["traceback"] = traceback.format_exc()
    
    logger.error(
        f"Error: {exc.message}",
        metadata=metadata
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for FastAPI HTTPException"""
    metadata = {
        "event": "http_exception", 
        "status_code": exc.status_code,
        "url": str(request.url),
        "method": request.method,
    }
    
    if config.environment == "development":
        # Include more detailed error info in development
        metadata["traceback"] = traceback.format_exc()
    
    logger.error(
        f"HTTPException: {exc.detail}",
        metadata=metadata
    )
    
    return JSONResponse(
        status_code=exc.status_code, 
        content={"error": exc.detail}
    )