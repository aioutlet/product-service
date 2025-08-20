# Error handling utilities

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.logger import logger


class ErrorResponse(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def error_response_handler(request: Request, exc: ErrorResponse):
    logger.error(
        f"Error: {exc.message}",
        extra={
            "event": "error_response",
            "status_code": exc.status_code,
            **exc.details,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTPException: {exc.detail}",
        extra={"event": "http_exception", "status_code": exc.status_code},
    )
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


class ErrorResponseModel(BaseModel):
    error: str
    details: dict = None
