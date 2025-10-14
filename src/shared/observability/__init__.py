"""
Observability module for Product Service
Provides unified logging, tracing, and monitoring capabilities

Structure:
- logging/ - Structured logging with correlation IDs
- tracing/ - Distributed tracing with OpenTelemetry
"""

# Re-export from submodules for convenience
from .logging import logger
from .tracing import tracer, get_current_span, initialize_tracing

__all__ = [
    'logger',
    'tracer',
    'get_current_span',
    'initialize_tracing',
]
