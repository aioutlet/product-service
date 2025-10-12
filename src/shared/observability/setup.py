"""
Observability setup and initialization for Product Service
"""

import os
import sys
from typing import Optional

from .helpers import create_log_directory, get_environment_context
from .logger import logger
from .tracing import initialize_tracing


def initialize_observability(app: Optional[object] = None) -> None:
    """
    Initialize complete observability system for Product Service
    
    Args:
        app: FastAPI application instance (optional)
    """
    try:
        # Get environment context
        env_context = get_environment_context()
        
        print(f"[{env_context['environment']}] Initializing observability system...")
        
        # Create log directory
        create_log_directory()
        
        # Initialize tracing first (before any other imports)
        initialize_tracing()
        
        # Initialize logger (this will log the initialization)
        logger.info(
            "Observability system initialized",
            metadata={
                "environment": env_context,
                "tracing": {
                    "enabled": env_context["tracingEnabled"],
                    "endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
                }
            }
        )
        
        # If FastAPI app is provided, instrument it
        if app:
            instrument_fastapi_app(app)
        
        print(f"[{env_context['environment']}] Observability system ready")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize observability: {e}", file=sys.stderr)
        # Don't raise the exception to avoid breaking the application
        # The logger will fall back to basic functionality


def instrument_fastapi_app(app) -> None:
    """
    Add observability middleware and handlers to FastAPI app
    """
    try:
        # Import here to avoid circular imports
        from .middleware import ObservabilityMiddleware
        
        # Add observability middleware
        app.add_middleware(ObservabilityMiddleware)
        
        logger.debug(
            "FastAPI app instrumented with observability middleware",
            metadata={"middleware": "ObservabilityMiddleware"}
        )
        
    except Exception as e:
        logger.error(
            "Failed to instrument FastAPI app",
            error=e,
            metadata={"component": "observability_setup"}
        )


def shutdown_observability() -> None:
    """
    Gracefully shutdown observability system
    """
    try:
        logger.info("Shutting down observability system")
        
        # Flush any pending logs
        import logging
        for handler in logging.getLogger().handlers:
            handler.flush()
        
        # Shutdown tracing
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry import trace
        
        tracer_provider = trace.get_tracer_provider()
        if isinstance(tracer_provider, TracerProvider):
            tracer_provider.shutdown()
        
        print("Observability system shutdown complete")
        
    except Exception as e:
        print(f"[ERROR] Failed to shutdown observability: {e}", file=sys.stderr)
