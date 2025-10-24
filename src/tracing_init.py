"""
Early tracing initialization for Product Service
This file must be imported before any other application modules
to ensure OpenTelemetry SDK is properly initialized for auto-instrumentation
"""

import os

# Set OpenTelemetry configuration early
SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

# Ensure environment variables are set before any imports
if not os.getenv("OTEL_SERVICE_NAME"):
    os.environ["OTEL_SERVICE_NAME"] = SERVICE_NAME

if not os.getenv("OTEL_SERVICE_VERSION"):
    os.environ["OTEL_SERVICE_VERSION"] = SERVICE_VERSION

# Set resource attributes
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"service.name={SERVICE_NAME},service.version={SERVICE_VERSION}"

# Enable auto-instrumentation
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"

if ENABLE_TRACING:
    try:
        # Import and initialize tracing early
        from src.observability.tracing import initialize_tracing
        initialize_tracing()
        print(f"[{SERVICE_NAME}] Early tracing initialization completed")
    except Exception as e:
        print(f"[{SERVICE_NAME}] Early tracing initialization failed: {e}")
else:
    print(f"[{SERVICE_NAME}] Tracing disabled by configuration")
