"""
Authentication and authorization dependencies for FastAPI.

Provides user authentication and role-based access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import os

from src.core.logger import logger


# Security scheme
security = HTTPBearer()

# JWT configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class CurrentUser:
    """
    Current authenticated user information.
    """
    def __init__(self, user_id: str, email: str, roles: list = None):
        self.user_id = user_id
        self.email = email
        self.roles = roles or []
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return "admin" in self.roles


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.
    
    Validates JWT token and extracts user information.
    
    Usage:
        @router.get("/products")
        async def list_products(current_user: CurrentUser = Depends(get_current_user)):
            logger.info(f"User {current_user.email} accessed products")
            ...
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        CurrentUser instance
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        user_id = payload.get("sub")
        email = payload.get("email")
        roles = payload.get("roles", [])
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        logger.debug(
            "User authenticated",
            metadata={"user_id": user_id, "email": email}
        )
        
        return CurrentUser(user_id=user_id, email=email, roles=roles)
    
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    
    except jwt.JWTError as e:
        logger.error("JWT validation error", error=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[CurrentUser]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise.
    
    Useful for endpoints that have optional authentication.
    
    Usage:
        @router.get("/products")
        async def list_products(current_user: Optional[CurrentUser] = Depends(get_optional_user)):
            if current_user:
                # User is authenticated
                pass
            else:
                # Anonymous access
                pass
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        CurrentUser instance if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Dependency factory to require specific role.
    
    Usage:
        @router.post("/products")
        async def create_product(
            product_data: dict,
            current_user: CurrentUser = Depends(require_role("admin"))
        ):
            ...
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_role(required_role):
            logger.warning(
                f"Access denied: user lacks required role",
                metadata={
                    "user_id": current_user.user_id,
                    "required_role": required_role,
                    "user_roles": current_user.roles
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires {required_role} role"
            )
        return current_user
    
    return role_checker


# Convenience dependency for admin-only endpoints
require_admin = require_role("admin")
