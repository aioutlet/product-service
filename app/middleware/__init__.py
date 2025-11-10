"""
Middleware modules for the Product Service
"""

from .trace_context import TraceContextMiddleware, get_trace_id, get_span_id

__all__ = ["TraceContextMiddleware", "get_trace_id", "get_span_id"]
