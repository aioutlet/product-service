"""
Unified logging schema and business event structures for Product Service
"""

import json
import os
import uuid
from datetime import datetime, UTC
from typing import Any, Dict, Optional, Union

from src.utils.correlation_id import get_correlation_id
from ..tracing import get_current_trace_id, get_current_span_id

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def create_base_log_entry(
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized base log entry with common fields
    """
    # Get tracing information
    trace_id = get_current_trace_id()
    span_id = get_current_span_id()
    
    # Get correlation ID
    if correlation_id is None:
        correlation_id = get_correlation_id()
    
    base_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level.upper(),
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "environment": ENVIRONMENT
        },
        "correlationId": correlation_id,
        "traceId": trace_id,
        "spanId": span_id,
        "message": message
    }
    
    # Add user context if available
    if user_id:
        base_entry["user"] = {"id": user_id}
    
    # Add any additional fields
    if kwargs:
        base_entry.update(kwargs)
    
    return base_entry


def create_business_event(
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized business event log entry
    """
    event_entry = create_base_log_entry(
        level="INFO",
        message=f"Business event: {event_type}",
        user_id=user_id,
        **kwargs
    )
    
    # Add business event specific fields
    event_entry["businessEvent"] = {
        "type": event_type,
        "eventId": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    # Add entity information if provided
    if entity_type and entity_id:
        event_entry["businessEvent"]["entity"] = {
            "type": entity_type,
            "id": entity_id
        }
    
    # Add metadata if provided
    if metadata:
        event_entry["businessEvent"]["metadata"] = metadata
    
    return event_entry


def create_operation_log(
    operation: str,
    status: str,  # "start", "success", "error"
    duration_ms: Optional[int] = None,
    error: Optional[Union[str, Exception]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized operation log entry
    """
    level = "ERROR" if status == "error" else "INFO"
    message = f"Operation {operation}: {status}"
    
    operation_entry = create_base_log_entry(
        level=level,
        message=message,
        **kwargs
    )
    
    # Add operation specific fields
    operation_entry["operation"] = {
        "name": operation,
        "status": status,
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    # Add duration if provided
    if duration_ms is not None:
        operation_entry["operation"]["durationMs"] = duration_ms
    
    # Add error information if provided
    if error:
        if isinstance(error, Exception):
            operation_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "details": getattr(error, 'args', None)
            }
        else:
            operation_entry["error"] = {"message": str(error)}
    
    # Add metadata if provided
    if metadata:
        operation_entry["operation"]["metadata"] = metadata
    
    return operation_entry


def create_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized security event log entry
    """
    security_entry = create_base_log_entry(
        level="WARN",
        message=f"Security event: {event_type}",
        user_id=user_id,
        **kwargs
    )
    
    # Add security event specific fields
    security_entry["securityEvent"] = {
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    # Add request context if provided
    if ip_address or user_agent:
        security_entry["request"] = {}
        if ip_address:
            security_entry["request"]["ipAddress"] = ip_address
        if user_agent:
            security_entry["request"]["userAgent"] = user_agent
    
    # Add metadata if provided
    if metadata:
        security_entry["securityEvent"]["metadata"] = metadata
    
    return security_entry


def create_performance_log(
    operation: str,
    duration_ms: int,
    threshold_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized performance log entry
    """
    is_slow = threshold_ms and duration_ms > threshold_ms
    level = "WARN" if is_slow else "INFO"
    message = f"Performance: {operation} took {duration_ms}ms"
    
    performance_entry = create_base_log_entry(
        level=level,
        message=message,
        **kwargs
    )
    
    # Add performance specific fields
    performance_entry["performance"] = {
        "operation": operation,
        "durationMs": duration_ms,
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    # Add threshold information if provided
    if threshold_ms:
        performance_entry["performance"]["thresholdMs"] = threshold_ms
        performance_entry["performance"]["exceededThreshold"] = is_slow
    
    # Add metadata if provided
    if metadata:
        performance_entry["performance"]["metadata"] = metadata
    
    return performance_entry


# Business event types for Product Service
class BusinessEvents:
    # Product events
    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"
    PRODUCT_DELETED = "PRODUCT_DELETED"
    PRODUCT_VIEWED = "PRODUCT_VIEWED"
    PRODUCT_SEARCHED = "PRODUCT_SEARCHED"
    
    # Category events
    CATEGORY_CREATED = "CATEGORY_CREATED"
    CATEGORY_UPDATED = "CATEGORY_UPDATED"
    CATEGORY_DELETED = "CATEGORY_DELETED"
    
    # Review events
    REVIEW_CREATED = "REVIEW_CREATED"
    REVIEW_UPDATED = "REVIEW_UPDATED"
    REVIEW_DELETED = "REVIEW_DELETED"
    
    # Inventory events
    INVENTORY_CHECKED = "INVENTORY_CHECKED"
    STOCK_UPDATED = "STOCK_UPDATED"
    
    # Cache events
    CACHE_HIT = "CACHE_HIT"
    CACHE_MISS = "CACHE_MISS"
    CACHE_INVALIDATED = "CACHE_INVALIDATED"


# Security event types for Product Service
class SecurityEvents:
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    INVALID_TOKEN = "INVALID_TOKEN"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    ADMIN_ACTION = "ADMIN_ACTION"


# Common operation names for Product Service
class Operations:
    # Product operations
    GET_PRODUCT = "get_product"
    LIST_PRODUCTS = "list_products"
    CREATE_PRODUCT = "create_product"
    UPDATE_PRODUCT = "update_product"
    DELETE_PRODUCT = "delete_product"
    SEARCH_PRODUCTS = "search_products"
    
    # Category operations
    GET_CATEGORIES = "get_categories"
    CREATE_CATEGORY = "create_category"
    UPDATE_CATEGORY = "update_category"
    DELETE_CATEGORY = "delete_category"
    
    # Review operations
    GET_REVIEWS = "get_reviews"
    CREATE_REVIEW = "create_review"
    UPDATE_REVIEW = "update_review"
    DELETE_REVIEW = "delete_review"
    
    # Database operations
    DB_QUERY = "db_query"
    DB_INSERT = "db_insert"
    DB_UPDATE = "db_update"
    DB_DELETE = "db_delete"
    
    # External service operations
    USER_SERVICE_CALL = "user_service_call"
    INVENTORY_SERVICE_CALL = "inventory_service_call"
    AUTH_SERVICE_CALL = "auth_service_call"
    
    # Cache operations
    CACHE_GET = "cache_get"
    CACHE_SET = "cache_set"
    CACHE_DELETE = "cache_delete"
