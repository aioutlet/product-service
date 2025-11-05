"""
Centralized logging configuration for Product Service.

This module consolidates logging functionality from both core/logger.py and observability/logger.py
to provide a unified logging interface with:
- Structured logging with correlation IDs
- Multiple log levels and formats
- Performance tracking
- Business and security event logging
- OpenTelemetry integration
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union

# Import correlation ID utilities
try:
    from src.utils.correlation_id import get_correlation_id
except ImportError:
    # Fallback if correlation_id not available
    def get_correlation_id() -> Optional[str]:
        return None

# Environment-based configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_PRODUCTION = ENVIRONMENT == "production"
IS_TEST = ENVIRONMENT == "test"

SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if IS_DEVELOPMENT else "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json" if IS_PRODUCTION else "console")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", f"logs/{SERVICE_NAME}.log")


class StructuredLogger:
    """
    Enhanced logger with structured logging, correlation IDs, and tracing support.
    Consolidates functionality from both legacy loggers.
    """
    
    def __init__(self):
        self.service_name = SERVICE_NAME
        self.environment = ENVIRONMENT
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure Python logging with handlers"""
        # Clear existing handlers
        logging.getLogger().handlers.clear()
        
        # Set log level
        logging.getLogger().setLevel(getattr(logging, LOG_LEVEL))
        
        # Console handler
        if LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, LOG_LEVEL))
            
            if LOG_FORMAT == "json":
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(ConsoleFormatter())
            
            logging.getLogger().addHandler(console_handler)
        
        # File handler
        if LOG_TO_FILE:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            
            file_handler = logging.FileHandler(LOG_FILE_PATH)
            file_handler.setLevel(getattr(logging, LOG_LEVEL))
            file_handler.setFormatter(JSONFormatter())  # Always JSON for files
            
            logging.getLogger().addHandler(file_handler)
    
    def _build_log_entry(
        self,
        level: str,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build structured log entry"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "service": self.service_name,
            "environment": self.environment,
            "message": message,
            "correlationId": correlation_id or get_correlation_id(),
        }
        
        if user_id:
            entry["userId"] = user_id
        
        if metadata:
            entry["metadata"] = metadata
        
        # Add any additional kwargs
        entry.update(kwargs)
        
        return entry
    
    def _log(
        self,
        level: str,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Internal logging method"""
        log_entry = self._build_log_entry(
            level, message, correlation_id, user_id, metadata, **kwargs
        )
        
        # Use Python logging
        log_method = getattr(logging.getLogger(), level.lower())
        
        if LOG_FORMAT == "json":
            log_method(json.dumps(log_entry))
        else:
            # Don't pass 'message' in extra to avoid conflict with LogRecord
            extra_data = {k: v for k, v in log_entry.items() if k != 'message'}
            log_method(message, extra=extra_data)
    
    def debug(
        self,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Debug level logging"""
        self._log("DEBUG", message, correlation_id, user_id, metadata, **kwargs)
    
    def info(
        self,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Info level logging"""
        self._log("INFO", message, correlation_id, user_id, metadata, **kwargs)
    
    def warning(
        self,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Warning level logging"""
        self._log("WARNING", message, correlation_id, user_id, metadata, **kwargs)
    
    def error(
        self,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        error: Optional[Union[str, Exception]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Error level logging"""
        if metadata is None:
            metadata = {}
        
        if error:
            if isinstance(error, Exception):
                metadata["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                }
            else:
                metadata["error"] = {"message": str(error)}
        
        self._log("ERROR", message, correlation_id, user_id, metadata, **kwargs)
    
    def critical(
        self,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        error: Optional[Union[str, Exception]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Critical level logging"""
        if metadata is None:
            metadata = {}
        
        if error:
            if isinstance(error, Exception):
                metadata["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                }
            else:
                metadata["error"] = {"message": str(error)}
        
        self._log("CRITICAL", message, correlation_id, user_id, metadata, **kwargs)
    
    def performance(
        self,
        operation: str,
        duration_ms: int,
        threshold_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log performance metrics"""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "operation": operation,
            "durationMs": duration_ms,
            "thresholdMs": threshold_ms,
        })
        
        level = "WARNING" if threshold_ms and duration_ms > threshold_ms else "INFO"
        self._log(level, f"Operation completed: {operation}", metadata=metadata, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName']:
                log_data[key] = value
        
        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        return f"{color}[{timestamp}] {record.levelname}{reset} - {record.getMessage()}"


# Create and export the logger instance
logger = StructuredLogger()

# Backward compatibility: export Python logger
py_logger = logging.getLogger(SERVICE_NAME)
