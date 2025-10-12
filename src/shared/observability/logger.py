"""
Enhanced logger for Product Service with correlation ID and tracing support
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional, Union

from .formatters import format_log_entry
from .helpers import (
    create_log_directory,
    get_log_config,
    get_service_info,
    is_slow_operation,
    should_log_level
)
from .schemas import (
    BusinessEvents,
    Operations,
    SecurityEvents,
    create_base_log_entry,
    create_business_event,
    create_operation_log,
    create_performance_log,
    create_security_event
)
from .tracing import add_span_attributes, set_span_status


class ProductServiceLogger:
    """
    Enhanced logger with correlation ID, tracing, and structured logging support
    """
    
    def __init__(self):
        self.config = get_log_config()
        self.service_info = get_service_info()
        
        # Create log directory if needed
        create_log_directory()
        
        # Set up Python logging
        self._setup_python_logging()
        
        # Log initialization
        self.info(
            "Logger initialized",
            metadata={
                "config": self.config,
                "service": self.service_info
            }
        )
    
    def _setup_python_logging(self):
        """
        Set up Python logging configuration
        """
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        # Set up console handler
        if self.config["toConsole"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.config["level"])
            logging.getLogger().addHandler(console_handler)
        
        # Set up file handler
        if self.config["toFile"]:
            file_handler = logging.FileHandler(self.config["filePath"])
            file_handler.setLevel(self.config["level"])
            logging.getLogger().addHandler(file_handler)
        
        # Set logging level
        logging.getLogger().setLevel(self.config["level"])
    
    def _log(
        self,
        level: str,
        message: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Internal logging method
        """
        if not should_log_level(level):
            return
        
        # Create log entry
        log_entry = create_base_log_entry(
            level=level,
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            **(metadata or {}),
            **kwargs
        )
        
        # Format log entry
        if self.config["toConsole"]:
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"]:
            file_output = format_log_entry(log_entry, "json")
            # Write to file using Python logging
            getattr(logging.getLogger(), level.lower())(file_output)
        
        # Add to current span if available
        if level.upper() in ["ERROR", "CRITICAL"]:
            set_span_status("ERROR", message)
            add_span_attributes({"error": True, "error.message": message})
    
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
        
        # Handle exception objects
        if error:
            if isinstance(error, Exception):
                metadata["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                    "args": getattr(error, 'args', None)
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
        
        # Handle exception objects
        if error:
            if isinstance(error, Exception):
                metadata["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                    "args": getattr(error, 'args', None)
                }
            else:
                metadata["error"] = {"message": str(error)}
        
        self._log("CRITICAL", message, correlation_id, user_id, metadata, **kwargs)
    
    def business(
        self,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log business events"""
        log_entry = create_business_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            metadata=metadata,
            **kwargs
        )
        
        # Format and output
        if self.config["toConsole"]:
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"]:
            file_output = format_log_entry(log_entry, "json")
            logging.getLogger().info(file_output)
        
        # Add to current span
        add_span_attributes({
            "business.event.type": event_type,
            "business.entity.type": entity_type,
            "business.entity.id": entity_id
        })
    
    def security(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log security events"""
        log_entry = create_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            **kwargs
        )
        
        # Format and output
        if self.config["toConsole"]:
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"]:
            file_output = format_log_entry(log_entry, "json")
            logging.getLogger().warning(file_output)
        
        # Add to current span
        add_span_attributes({
            "security.event.type": event_type,
            "security.user.id": user_id,
            "security.request.ip": ip_address
        })
    
    def operation_start(
        self,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> float:
        """Log operation start and return start time"""
        start_time = time.time()
        
        log_entry = create_operation_log(
            operation=operation,
            status="start",
            metadata=metadata,
            **kwargs
        )
        
        if self.config["toConsole"] and should_log_level("DEBUG"):
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"] and should_log_level("DEBUG"):
            file_output = format_log_entry(log_entry, "json")
            logging.getLogger().debug(file_output)
        
        # Add to current span
        add_span_attributes({"operation.name": operation, "operation.status": "start"})
        
        return start_time
    
    def operation_complete(
        self,
        operation: str,
        start_time: float,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> int:
        """Log operation completion and return duration in milliseconds"""
        duration_ms = int((time.time() - start_time) * 1000)
        
        log_entry = create_operation_log(
            operation=operation,
            status="success",
            duration_ms=duration_ms,
            metadata=metadata,
            **kwargs
        )
        
        # Check if operation is slow
        if is_slow_operation(operation, duration_ms):
            log_entry["level"] = "WARNING"
        
        if self.config["toConsole"]:
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"]:
            file_output = format_log_entry(log_entry, "json")
            level = "warning" if is_slow_operation(operation, duration_ms) else "info"
            getattr(logging.getLogger(), level)(file_output)
        
        # Add to current span
        add_span_attributes({
            "operation.name": operation,
            "operation.status": "success",
            "operation.duration_ms": duration_ms
        })
        
        set_span_status("OK")
        
        return duration_ms
    
    def operation_failed(
        self,
        operation: str,
        start_time: float,
        error: Union[str, Exception],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> int:
        """Log operation failure and return duration in milliseconds"""
        duration_ms = int((time.time() - start_time) * 1000)
        
        log_entry = create_operation_log(
            operation=operation,
            status="error",
            duration_ms=duration_ms,
            error=error,
            metadata=metadata,
            **kwargs
        )
        
        if self.config["toConsole"]:
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"]:
            file_output = format_log_entry(log_entry, "json")
            logging.getLogger().error(file_output)
        
        # Add to current span
        error_message = str(error)
        add_span_attributes({
            "operation.name": operation,
            "operation.status": "error",
            "operation.duration_ms": duration_ms,
            "error": True,
            "error.message": error_message
        })
        
        set_span_status("ERROR", error_message)
        
        return duration_ms
    
    def performance(
        self,
        operation: str,
        duration_ms: int,
        threshold_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log performance metrics"""
        log_entry = create_performance_log(
            operation=operation,
            duration_ms=duration_ms,
            threshold_ms=threshold_ms,
            metadata=metadata,
            **kwargs
        )
        
        if self.config["toConsole"]:
            console_output = format_log_entry(log_entry, "console")
            print(console_output)
        
        if self.config["toFile"]:
            file_output = format_log_entry(log_entry, "json")
            level = "warning" if threshold_ms and duration_ms > threshold_ms else "info"
            getattr(logging.getLogger(), level)(file_output)
        
        # Add to current span
        add_span_attributes({
            "performance.operation": operation,
            "performance.duration_ms": duration_ms,
            "performance.threshold_ms": threshold_ms
        })


# Create and export the logger instance
logger = ProductServiceLogger()

# Export constants for convenience
logger.BusinessEvents = BusinessEvents
logger.SecurityEvents = SecurityEvents
logger.Operations = Operations
