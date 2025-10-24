"""
Tracing module for Product Service
Provides distributed tracing with OpenTelemetry
"""

from .tracer import (
    initialize_tracing,
    tracer,
    get_current_span,
    get_current_trace_id,
    get_current_span_id,
    create_span_context,
    add_span_attributes,
    set_span_status,
)

__all__ = [
    "initialize_tracing",
    "tracer",
    "get_current_span",
    "get_current_trace_id",
    "get_current_span_id",
    "create_span_context",
    "add_span_attributes",
    "set_span_status",
]
