"""
OpenTelemetry Tracing Configuration
Configures W3C Trace Context propagation for distributed tracing across microservices
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from app.core.config import config
from app.core.logger import logger


_initialized = False


def init_telemetry() -> Optional[TracerProvider]:
    """
    Initialize OpenTelemetry tracing with W3C Trace Context propagation
    
    Returns:
        TracerProvider if tracing is enabled, None otherwise
    """
    global _initialized
    
    if _initialized:
        logger.warning("OpenTelemetry already initialized, skipping")
        return trace.get_tracer_provider()
    
    if not config.enable_tracing:
        logger.info("Distributed tracing is disabled")
        return None
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": config.service_name,
            "service.version": config.service_version,
            "service.environment": config.environment,
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Configure OTLP exporter (for Jaeger, Zipkin, or other OTLP-compatible backends)
        if config.otel_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=config.otel_endpoint,
                timeout=5  # 5 second timeout
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP span exporter configured: {config.otel_endpoint}")
        else:
            logger.warning("No OTLP endpoint configured, spans will not be exported")
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument logging to include trace context
        LoggingInstrumentor().instrument(set_logging_format=True)
        
        logger.info(
            "OpenTelemetry initialized successfully",
            extra={
                "service_name": config.service_name,
                "otel_endpoint": config.otel_endpoint,
                "trace_sample_rate": config.trace_sample_rate
            }
        )
        
        _initialized = True
        return tracer_provider
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        return None


def instrument_app(app):
    """
    Instrument FastAPI application with OpenTelemetry
    
    Args:
        app: FastAPI application instance
    """
    if not config.enable_tracing:
        return
    
    try:
        # Instrument FastAPI for automatic span creation
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
        
        # Instrument HTTPX client for outgoing HTTP requests
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX client instrumented with OpenTelemetry")
        
        # Instrument PyMongo for database operations
        PymongoInstrumentor().instrument()
        logger.info("PyMongo instrumented with OpenTelemetry")
        
    except Exception as e:
        logger.error(f"Failed to instrument application: {e}", exc_info=True)


def get_current_span():
    """Get the current active span from the trace context"""
    return trace.get_current_span()


def get_trace_context():
    """
    Get the current trace context (traceId and spanId) as a dictionary
    
    Returns:
        dict: {"trace_id": str, "span_id": str} or None if no active span
    """
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        context = span.get_span_context()
        return {
            "trace_id": format(context.trace_id, '032x'),
            "span_id": format(context.span_id, '016x'),
        }
    return None
