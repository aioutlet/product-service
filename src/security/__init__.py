"""
Security package for FastAPI authentication and authorization
"""

from .dependencies import (
    User,
    get_current_user,
    get_optional_user,
    require_admin,
    require_customer,
    require_roles,
    verify_admin_access,
    verify_user_or_admin,
)

__all__ = [
    "User",
    "get_current_user",
    "get_optional_user",
    "require_admin",
    "require_customer",
    "require_roles",
    "verify_admin_access",
    "verify_user_or_admin",
]
