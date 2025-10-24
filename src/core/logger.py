"""
Standardized logger configuration for Python FastAPI services
Supports both development and production environments with correlation ID integration
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from src.utils.correlation_id import get_correlation_id

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
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", f"{SERVICE_NAME}.log")


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
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
                "correlationId",
                "userId",
                "operation",
                "duration",
            ]:
                if value is not None:
                    json_val = (
                        json.dumps(value) if isinstance(value, (dict, list)) else value
                    )
                    meta_fields.append(f"{key}={json_val}")

        meta_str = f" | {', '.join(meta_fields)}" if meta_fields else ""

        base_msg = (
            f"[{timestamp}] [{record.levelname}] {SERVICE_NAME} "
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
            "service": SERVICE_NAME,
            "correlationId": correlation_id,
            "message": record.getMessage(),
        }

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if (
                key
                not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "getMessage",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "message",
                    "message",
                ]
                and value is not None
            ):
                log_record[key] = value

        return json.dumps(log_record, default=str)


class StandardLogger:
    """Enhanced logger with correlation ID and metadata support"""

    def __init__(self):
        self.logger = logging.getLogger(SERVICE_NAME)
        self.logger.setLevel(LOG_LEVEL)

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Add console handler
        if LOG_TO_CONSOLE and not IS_TEST:
            console_handler = logging.StreamHandler()
            if LOG_FORMAT == "json":
                console_handler.setFormatter(JsonFormatter())
            else:
                console_handler.setFormatter(ColorFormatter())
            self.logger.addHandler(console_handler)

        # Add file handler
        if LOG_TO_FILE:
            file_handler = logging.FileHandler(LOG_FILE_PATH)
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

        # Log initialization
        self._log(
            "info",
            "Logger initialized",
            metadata={
                "logLevel": LOG_LEVEL,
                "logFormat": LOG_FORMAT,
                "logToFile": LOG_TO_FILE,
                "logToConsole": LOG_TO_CONSOLE,
                "environment": ENVIRONMENT,
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

    def fatal(
        self, message: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Fatal level logging (maps to critical)"""
        if metadata is None:
            metadata = {}
        metadata["level"] = "FATAL"
        self._log("critical", message, request, metadata)

    def operation_start(
        self, operation: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Log operation start and return start time"""
        import time

        start_time = time.time()
        if metadata is None:
            metadata = {}
        metadata.update({"operation": operation, "operationStart": True, **metadata})
        self.debug(f"Starting operation: {operation}", request, metadata)
        return start_time

    def operation_complete(
        self,
        operation: str,
        start_time: float,
        request=None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Log operation completion and return duration"""
        import time

        duration = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        if metadata is None:
            metadata = {}
        metadata.update(
            {
                "operation": operation,
                "duration": duration,
                "operationComplete": True,
                **metadata,
            }
        )
        self.info(f"Completed operation: {operation}", request, metadata)
        return duration

    def operation_failed(
        self,
        operation: str,
        start_time: float,
        error,
        request=None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Log operation failure and return duration"""
        import time

        duration = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        if metadata is None:
            metadata = {}
        metadata.update(
            {
                "operation": operation,
                "duration": duration,
                "error": error,
                "operationFailed": True,
                **metadata,
            }
        )
        self.error(f"Failed operation: {operation}", request, metadata)
        return duration

    def business(
        self, event: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Log business events"""
        if metadata is None:
            metadata = {}
        metadata.update({"businessEvent": event, **metadata})
        self.info(f"Business event: {event}", request, metadata)

    def security(
        self, event: str, request=None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security events"""
        if metadata is None:
            metadata = {}
        metadata.update({"securityEvent": event, **metadata})
        self.warning(f"Security event: {event}", request, metadata)

    def performance(
        self,
        operation: str,
        duration: int,
        request=None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log performance metrics"""
        if metadata is None:
            metadata = {}
        metadata.update(
            {
                "operation": operation,
                "duration": duration,
                "performance": True,
                **metadata,
            }
        )
        level = "warning" if duration > 1000 else "info"
        self._log(level, f"Performance: {operation}", request, metadata)


# Create and export the standard logger instance
logger = StandardLogger()


# Legacy compatibility - export individual functions
def info(message: str, metadata: Optional[Dict[str, Any]] = None):
    logger.info(message, metadata=metadata)


def debug(message: str, metadata: Optional[Dict[str, Any]] = None):
    logger.debug(message, metadata=metadata)


def warning(message: str, metadata: Optional[Dict[str, Any]] = None):
    logger.warning(message, metadata=metadata)


def error(message: str, metadata: Optional[Dict[str, Any]] = None):
    logger.error(message, metadata=metadata)
