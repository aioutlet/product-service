"""
Middleware modules for the Product Service
"""

from .correlation_id import CorrelationIdMiddleware, get_correlation_id

__all__ = ["CorrelationIdMiddleware", "get_correlation_id"]
