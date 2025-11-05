"""
Shared middlewares module for product-service.
Contains middlewares that can be used by both API and Consumer.
"""

from .correlation_id import CorrelationIdMiddleware

__all__ = ["CorrelationIdMiddleware"]
