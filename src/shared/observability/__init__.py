"""
Observability module for Product Service
Provides unified logging, tracing, and monitoring capabilities
"""

from .setup import initialize_observability
from .logger import logger
from .tracing import tracer, get_current_span

__all__ = ['initialize_observability', 'logger', 'tracer', 'get_current_span']
