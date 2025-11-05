"""
Shared utilities package
"""

from .correlation_id import (
    get_correlation_id,
    set_correlation_id,
    create_correlation_id,
    create_headers_with_correlation_id,
    extract_correlation_id_from_headers,
)
from .dependency_health_checker import (
    check_database_health,
    check_dependency_health,
    get_dependencies,
)

__all__ = [
    # Correlation ID utilities
    "get_correlation_id",
    "set_correlation_id",
    "create_correlation_id",
    "create_headers_with_correlation_id",
    "extract_correlation_id_from_headers",
    # Dependency health checker
    "check_database_health",
    "check_dependency_health",
    "get_dependencies",
]
