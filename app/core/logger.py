"""
Standardized logger configuration for FastAPI services
Supports both development and production environments with correlation ID integration
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import config

# Import correlation ID utility from middleware
try:
    from app.middleware.correlation_id import get_correlation_id
except ImportError:
    # Fallback if middleware not available yet
    def get_correlation_id() -> Optional[str]:
        """Get correlation ID from context - placeholder for now"""
        return None

# Environment-based configuration
IS_DEVELOPMENT = config.environment == "development"
IS_PRODUCTION = config.environment == "production"
IS_TEST = config.environment == "test"


class ColorFormatter(logging.Formatter):
    """Colored formatter for development console output"""

    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        # Build the base message with standard fields
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        correlation_id = getattr(record, "correlationId", None) or get_correlation_id()
        corr_id_str = f"[{correlation_id}]" if correlation_id else "[no-correlation]"

        # Build metadata string
        meta_fields = []
        if hasattr(record, "userId") and record.userId:
            meta_fields.append(f"userId={record.userId}")
        if hasattr(record, "operation") and record.operation:
            meta_fields.append(f"operation={record.operation}")
        if hasattr(record, "duration") and record.duration:
            meta_fields.append(f"duration={record.duration}ms")

        # Add extra metadata
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage",
                "exc_info", "exc_text", "stack_info", "message", "correlationId",
                "userId", "operation", "duration",
            ]:
                if value is not None:
                    json_val = (
                        json.dumps(value) if isinstance(value, (dict, list)) else value
                    )
                    meta_fields.append(f"{key}={json_val}")

        meta_str = f" | {', '.join(meta_fields)}" if meta_fields else ""

        base_msg = (
            f"[{timestamp}] [{record.levelname}] {config.service_name} "
            f"{corr_id_str}: {record.getMessage()}{meta_str}"
        )

        # Apply color if in development and terminal supports it
        if IS_DEVELOPMENT and sys.stdout.isatty() and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            base_msg = f"{color}{base_msg}{self.RESET}"

        return base_msg


class JsonFormatter(logging.Formatter):
    """JSON formatter for production logging"""

    def format(self, record):
        correlation_id = getattr(record, "correlationId", None) or get_correlation_id()

        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "service": config.service_name,
            "correlationId": correlation_id,
            "message": record.getMessage(),
        }

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if (
                key not in [
                    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                    "module", "lineno", "funcName", "created", "msecs", "relativeCreated",
                    "thread", "threadName", "processName", "process", "getMessage",
                    "exc_info", "exc_text", "stack_info", "message",
                ]
                and value is not None
            ):
                log_record[key] = value

        return json.dumps(log_record, default=str)


class StandardLogger:
    """Enhanced logger with correlation ID and metadata support"""

    def __init__(self):
        self.logger = logging.getLogger(config.service_name)
        self.logger.setLevel(config.log_level)

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Add console handler
        if config.log_to_console and not IS_TEST:
            console_handler = logging.StreamHandler()
            if config.log_format == "json":
                console_handler.setFormatter(JsonFormatter())
            else:
                console_handler.setFormatter(ColorFormatter())
            self.logger.addHandler(console_handler)

        # Add file handler
        if config.log_to_file:
            file_handler = logging.FileHandler(f"{config.service_name}.log")
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

        # Log initialization
        self._log(
            "info",
            "Logger initialized",
            metadata={
                "logLevel": config.log_level,
                "logFormat": config.log_format,
                "logToFile": config.log_to_file,
                "logToConsole": config.log_to_console,
                "environment": config.environment,
            },
        )

    def _log(
        self,
        level: str,
        message: str,
        request=None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Internal logging method with standard fields"""
        if metadata is None:
            metadata = {}

        # Build log data
        log_data = {
            "correlationId": metadata.get("correlationId") or get_correlation_id(),
            "userId": metadata.get("userId"),
            "operation": metadata.get("operation"),
            "duration": metadata.get("duration"),
            **metadata,
        }

        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}

        # Create log record with extra data
        getattr(self.logger, level.lower())(message, extra=log_data)

    def info(
        self, message: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Info level logging"""
        self._log("info", message, request, metadata)

    def debug(
        self, message: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Debug level logging"""
        self._log("debug", message, request, metadata)

    def warning(
        self, message: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Warning level logging"""
        self._log("warning", message, request, metadata)

    def error(
        self, message: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Error level logging"""
        if metadata is None:
            metadata = {}

        # Handle exception objects
        if "error" in metadata and isinstance(metadata["error"], Exception):
            metadata["error"] = {
                "type": type(metadata["error"]).__name__,
                "message": str(metadata["error"]),
                "args": metadata["error"].args,
            }

        self._log("error", message, request, metadata)


# Create and export the standard logger instance
logger = StandardLogger()