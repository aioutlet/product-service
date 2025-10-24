"""
Output formatters for different logging environments
"""

import json
import os
import sys
from datetime import datetime, UTC
from typing import Any, Dict


# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
LOG_FORMAT = os.getenv("LOG_FORMAT", "console" if ENVIRONMENT == "development" else "json")


class ConsoleFormatter:
    """
    Human-readable formatter for development console output
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[94m",    # Blue
        "INFO": "\033[92m",     # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",    # Red
        "CRITICAL": "\033[95m", # Magenta
    }
    RESET = "\033[0m"
    
    @classmethod
    def format(cls, log_data: Dict[str, Any]) -> str:
        """
        Format log data for console output
        """
        # Extract basic fields
        timestamp = log_data.get("timestamp", datetime.now(UTC).isoformat())
        level = log_data.get("level", "INFO")
        message = log_data.get("message", "")
        correlation_id = log_data.get("correlationId", "no-correlation")
        trace_id = log_data.get("traceId")
        span_id = log_data.get("spanId")
        
        # Build correlation/trace info
        trace_info = f"[{correlation_id}]"
        if trace_id and span_id:
            trace_info = f"[{correlation_id}] [{trace_id[:8]}:{span_id[:8]}]"
        
        # Build metadata string
        meta_parts = []
        
        # Add user info
        if "user" in log_data and log_data["user"]:
            user_id = log_data["user"].get("id")
            if user_id:
                meta_parts.append(f"user={user_id}")
        
        # Add operation info
        if "operation" in log_data:
            op = log_data["operation"]
            if isinstance(op, dict):
                op_name = op.get("name")
                duration = op.get("durationMs")
                if op_name:
                    op_str = op_name
                    if duration:
                        op_str += f"({duration}ms)"
                    meta_parts.append(f"op={op_str}")
            elif isinstance(op, str):
                meta_parts.append(f"op={op}")
        
        # Add business event info
        if "businessEvent" in log_data:
            event = log_data["businessEvent"]
            if isinstance(event, dict):
                event_type = event.get("type")
                if event_type:
                    meta_parts.append(f"event={event_type}")
        
        # Add security event info
        if "securityEvent" in log_data:
            event = log_data["securityEvent"]
            if isinstance(event, dict):
                event_type = event.get("type")
                if event_type:
                    meta_parts.append(f"security={event_type}")
        
        # Add error info
        if "error" in log_data:
            error = log_data["error"]
            if isinstance(error, dict):
                error_type = error.get("type", "Error")
                meta_parts.append(f"error={error_type}")
        
        # Add performance info
        if "performance" in log_data:
            perf = log_data["performance"]
            if isinstance(perf, dict):
                duration = perf.get("durationMs")
                if duration:
                    meta_parts.append(f"perf={duration}ms")
        
        # Build final message
        meta_str = f" | {', '.join(meta_parts)}" if meta_parts else ""
        base_msg = f"[{timestamp}] [{level}] {SERVICE_NAME} {trace_info}: {message}{meta_str}"
        
        # Apply color if in development and terminal supports it
        if ENVIRONMENT == "development" and sys.stdout.isatty() and level in cls.COLORS:
            color = cls.COLORS[level]
            base_msg = f"{color}{base_msg}{cls.RESET}"
        
        return base_msg


class JsonFormatter:
    """
    JSON formatter for production logging and log aggregation
    """
    
    @classmethod
    def format(cls, log_data: Dict[str, Any]) -> str:
        """
        Format log data as JSON
        """
        # Ensure required fields are present
        if "timestamp" not in log_data:
            log_data["timestamp"] = datetime.now(UTC).isoformat()
        
        if "level" not in log_data:
            log_data["level"] = "INFO"
        
        if "service" not in log_data:
            log_data["service"] = {
                "name": SERVICE_NAME,
                "version": os.getenv("SERVICE_VERSION", "1.0.0"),
                "environment": ENVIRONMENT
            }
        
        # Convert to JSON string
        return json.dumps(log_data, default=str, ensure_ascii=False)


def format_log_entry(log_data: Dict[str, Any], format_type: str = None) -> str:
    """
    Format a log entry based on the specified format type
    """
    if format_type is None:
        format_type = LOG_FORMAT
    
    if format_type.lower() == "json":
        return JsonFormatter.format(log_data)
    else:
        return ConsoleFormatter.format(log_data)
