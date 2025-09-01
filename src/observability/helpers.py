"""
Environment-specific configuration and utilities
"""

import os
from typing import Any, Dict, Optional


# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_DEVELOPMENT = ENVIRONMENT in ["development", "local"]
IS_PRODUCTION = ENVIRONMENT == "production"
IS_TEST = ENVIRONMENT == "test"

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if IS_DEVELOPMENT else "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "console" if IS_DEVELOPMENT else "json")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", f"./logs/{SERVICE_NAME}-{ENVIRONMENT}.log")

# Tracing configuration
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"
OTEL_EXPORTER_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

# Correlation ID configuration
CORRELATION_ID_HEADER = os.getenv("CORRELATION_ID_HEADER", "x-correlation-id")


def get_service_info() -> Dict[str, str]:
    """
    Get standard service information
    """
    return {
        "name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": ENVIRONMENT
    }


def get_log_config() -> Dict[str, Any]:
    """
    Get logging configuration
    """
    return {
        "level": LOG_LEVEL,
        "format": LOG_FORMAT,
        "toFile": LOG_TO_FILE,
        "toConsole": LOG_TO_CONSOLE,
        "filePath": LOG_FILE_PATH,
        "environment": ENVIRONMENT
    }


def get_tracing_config() -> Dict[str, Any]:
    """
    Get tracing configuration
    """
    return {
        "enabled": ENABLE_TRACING,
        "endpoint": OTEL_EXPORTER_ENDPOINT,
        "serviceName": SERVICE_NAME,
        "serviceVersion": SERVICE_VERSION,
        "environment": ENVIRONMENT
    }


def should_log_level(level: str) -> bool:
    """
    Check if a log level should be logged based on current configuration
    """
    level_hierarchy = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    current_level = level_hierarchy.get(LOG_LEVEL.upper(), 20)
    check_level = level_hierarchy.get(level.upper(), 20)
    
    return check_level >= current_level


def create_log_directory():
    """
    Create log directory if it doesn't exist
    """
    if LOG_TO_FILE:
        log_dir = os.path.dirname(LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"[{SERVICE_NAME}] Created log directory: {log_dir}")


def get_environment_context() -> Dict[str, Any]:
    """
    Get environment context for logging
    """
    return {
        "environment": ENVIRONMENT,
        "isDevelopment": IS_DEVELOPMENT,
        "isProduction": IS_PRODUCTION,
        "isTest": IS_TEST,
        "logLevel": LOG_LEVEL,
        "tracingEnabled": ENABLE_TRACING
    }


# Performance thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    "database_query": 100,
    "external_api_call": 500,
    "cache_operation": 10,
    "file_operation": 50,
    "default": 1000
}


def get_performance_threshold(operation: str) -> int:
    """
    Get performance threshold for a specific operation
    """
    return PERFORMANCE_THRESHOLDS.get(operation.lower(), PERFORMANCE_THRESHOLDS["default"])


def is_slow_operation(operation: str, duration_ms: int) -> bool:
    """
    Check if an operation is considered slow
    """
    threshold = get_performance_threshold(operation)
    return duration_ms > threshold
