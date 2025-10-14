"""
Logging module for Product Service
Provides structured logging with correlation ID support
"""

from .logger import logger, ProductServiceLogger
from .formatters import format_log_entry
from .schemas import (
    BusinessEvents,
    Operations,
    SecurityEvents,
    create_base_log_entry,
    create_business_event,
    create_operation_log,
    create_performance_log,
    create_security_event,
)

__all__ = [
    "logger",
    "ProductServiceLogger",
    "format_log_entry",
    "BusinessEvents",
    "Operations",
    "SecurityEvents",
    "create_base_log_entry",
    "create_business_event",
    "create_operation_log",
    "create_performance_log",
    "create_security_event",
]
