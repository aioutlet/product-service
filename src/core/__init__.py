"""
Core utilities package.

Centralized core components for the Product Service:
- database: MongoDB connection and utilities
- security: Authentication and authorization
- logger: Structured logging with correlation IDs
- errors: Custom exception classes and handlers
"""

# Database
from .database import get_db, get_product_collection

# Errors
from .errors import (
    ErrorResponse,
    ErrorResponseModel,
    error_response_handler,
    http_exception_handler,
)

# Logger
from .logger import logger, py_logger

# Security
from .security import (
    User,
    get_current_user,
    get_optional_user,
    require_roles,
    require_admin,
    require_customer,
    verify_admin_access,
    verify_user_or_admin,
)

__all__ = [
    # Database
    "get_db",
    "get_product_collection",
    # Errors
    "ErrorResponse",
    "ErrorResponseModel",
    "error_response_handler",
    "http_exception_handler",
    # Logger
    "logger",
    "py_logger",
    # Security
    "User",
    "get_current_user",
    "get_optional_user",
    "require_roles",
    "require_admin",
    "require_customer",
    "verify_admin_access",
    "verify_user_or_admin",
]
