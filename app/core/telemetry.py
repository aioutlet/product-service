"""
OpenTelemetry Instrumentation for FastAPI

Works alongside Dapr for automatic span creation and trace enrichment.
Dapr handles trace context propagation and OTLP export (configured in .dapr/config.yaml)
"""

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from app.core.logger import logger


def instrument_app(app):
    """
    Instrument FastAPI application with OpenTelemetry for automatic span creation.
    
    Note: Dapr handles trace context propagation and OTLP export.
    This instrumentation creates spans for local operations.
    
    Args:
        app: FastAPI application instance
    """
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
        
        logger.info("OpenTelemetry instrumentation complete (trace export handled by Dapr)")
        
    except Exception as e:
        logger.error(f"Failed to instrument application: {e}", exc_info=True)
