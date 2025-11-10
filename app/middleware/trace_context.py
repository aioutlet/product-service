"""
W3C Trace Context Middleware
Implements W3C Trace Context standard for distributed tracing
Extracts/generates traceparent header and propagates trace context
"""

import uuid
import re
from contextvars import ContextVar
from typing import Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables to store trace context for the current request
trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_ctx: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


def get_trace_id() -> Optional[str]:
    """Get the trace ID from the current context"""
    return trace_id_ctx.get()


def get_span_id() -> Optional[str]:
    """Get the span ID from the current context"""
    return span_id_ctx.get()


def set_trace_context(trace_id: str, span_id: str) -> None:
    """Set the trace context in the current context"""
    trace_id_ctx.set(trace_id)
    span_id_ctx.set(span_id)


def extract_trace_context(traceparent: str) -> Optional[Tuple[str, str]]:
    """
    Extract traceId and spanId from W3C traceparent header
    Format: 00-{32-hex-traceId}-{16-hex-spanId}-{2-hex-flags}
    
    Args:
        traceparent: W3C traceparent header value
        
    Returns:
        Tuple of (trace_id, span_id) or None if invalid
    """
    if not traceparent:
        return None
    
    # W3C Trace Context format: version-trace_id-span_id-trace_flags
    pattern = r'^00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}$'
    match = re.match(pattern, traceparent)
    
    if match:
        trace_id, span_id = match.groups()
        # Validate not all zeros
        if trace_id != '0' * 32 and span_id != '0' * 16:
            return (trace_id, span_id)
    
    return None


def generate_trace_context() -> Tuple[str, str]:
    """
    Generate new trace context (traceId and spanId)
    
    Returns:
        Tuple of (trace_id, span_id) as 32-char and 16-char hex strings
    """
    trace_id = uuid.uuid4().hex  # 32 hex chars
    span_id = uuid.uuid4().hex[:16]  # 16 hex chars
    return (trace_id, span_id)


class TraceContextMiddleware(BaseHTTPMiddleware):
    """
    W3C Trace Context Middleware
    
    - Extracts W3C traceparent header from incoming requests
    - Generates new trace context if none provided
    - Stores trace context in request state
    - Propagates traceparent header in responses
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract W3C Trace Context from traceparent header
        traceparent = request.headers.get("traceparent")
        trace_context = extract_trace_context(traceparent) if traceparent else None
        
        if trace_context:
            trace_id, span_id = trace_context
        else:
            # Generate new trace context
            trace_id, span_id = generate_trace_context()
        
        # Store in context and request state
        set_trace_context(trace_id, span_id)
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        
        # Process the request
        response = await call_next(request)
        
        # Add W3C traceparent header to response
        traceparent_response = f"00-{trace_id}-{span_id}-01"
        response.headers["traceparent"] = traceparent_response
        response.headers["X-Trace-ID"] = trace_id
        
        return response
