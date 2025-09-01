"""
Distributed tracing setup for Product Service using OpenTelemetry
"""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Tracing configuration
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"
OTEL_EXPORTER_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

# Global tracer instance
tracer = None


def initialize_tracing():
    """
    Initialize OpenTelemetry tracing for the Product Service
    """
    global tracer
    
    if not ENABLE_TRACING:
        print(f"[{SERVICE_NAME}] Tracing disabled by configuration")
        return
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "service.version": SERVICE_VERSION,
            "service.environment": ENVIRONMENT,
        })
        
        # Set up the tracer provider
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_ENDPOINT)
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace_provider.add_span_processor(span_processor)
        
        # Get tracer instance
        tracer = trace.get_tracer(SERVICE_NAME, SERVICE_VERSION)
        
        # Auto-instrument libraries
        instrument_libraries()
        
        print(f"[{SERVICE_NAME}] Tracing initialized with endpoint: {OTEL_EXPORTER_ENDPOINT}")
        
    except Exception as e:
        print(f"[{SERVICE_NAME}] Failed to initialize tracing: {e}")
        tracer = trace.get_tracer(SERVICE_NAME, SERVICE_VERSION)  # Fallback tracer


def instrument_libraries():
    """
    Auto-instrument supported libraries
    """
    try:
        # Instrument FastAPI
        FastAPIInstrumentor().instrument()
        
        # Instrument HTTP client
        HTTPXClientInstrumentor().instrument()
        
        # Instrument MongoDB
        PymongoInstrumentor().instrument()
        
        # Instrument Redis
        RedisInstrumentor().instrument()
        
        # Instrument logging
        LoggingInstrumentor().instrument(set_logging_format=True)
        
        print(f"[{SERVICE_NAME}] Libraries instrumented successfully")
        
    except Exception as e:
        print(f"[{SERVICE_NAME}] Failed to instrument libraries: {e}")


def get_current_span():
    """
    Get the current active span
    """
    return trace.get_current_span()


def get_current_trace_id() -> Optional[str]:
    """
    Get the current trace ID as a string
    """
    try:
        span = get_current_span()
        if span and span.is_recording():
            trace_id = span.get_span_context().trace_id
            if trace_id and trace_id != 0:
                return format(trace_id, '032x')
    except Exception as e:
        print(f"[{SERVICE_NAME}] Error getting trace ID: {e}")
    return None


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID as a string
    """
    try:
        span = get_current_span()
        if span and span.is_recording():
            span_id = span.get_span_context().span_id
            if span_id and span_id != 0:
                return format(span_id, '016x')
    except Exception as e:
        print(f"[{SERVICE_NAME}] Error getting span ID: {e}")
    return None


def create_span(name: str, attributes: Optional[dict] = None):
    """
    Create a new span with optional attributes
    """
    if not tracer:
        span = trace.get_tracer(SERVICE_NAME).start_span(name)
    else:
        span = tracer.start_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    return span


def create_span_context(name: str, attributes: Optional[dict] = None):
    """
    Create a new span context manager with optional attributes
    """
    from opentelemetry.trace import use_span
    
    if not tracer:
        tracer_instance = trace.get_tracer(SERVICE_NAME)
    else:
        tracer_instance = tracer
    
    span = tracer_instance.start_span(name)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    # Return a context manager that properly sets the span as current
    return use_span(span, end_on_exit=True)


def add_span_attributes(attributes: dict):
    """
    Add attributes to the current span
    """
    span = get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[dict] = None):
    """
    Add an event to the current span
    """
    span = get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def set_span_status(status_code: str, description: Optional[str] = None):
    """
    Set the status of the current span
    """
    span = get_current_span()
    if span and span.is_recording():
        from opentelemetry.trace import Status, StatusCode
        
        # Map string status codes to OpenTelemetry status codes
        status_mapping = {
            "OK": StatusCode.OK,
            "ERROR": StatusCode.ERROR,
            "UNSET": StatusCode.UNSET
        }
        
        status_code_enum = status_mapping.get(status_code.upper(), StatusCode.UNSET)
        span.set_status(Status(status_code_enum, description))


# Initialize tracing if not already done
if tracer is None:
    initialize_tracing()
