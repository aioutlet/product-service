"""
FastAPI Security Dependencies for JWT Authentication and Authorization
Following FastAPI best practices with dependency injection pattern
"""

import os
from typing import Optional, List, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from src.shared.observability.logging import logger

# JWT Configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# FastAPI security scheme
security = HTTPBearer()


class User(dict):
    """Type-safe user object returned by authentication"""
    @property
    def user_id(self) -> str:
        return self["user_id"]
    
    @property
    def email(self) -> Optional[str]:
        return self.get("email")
    
    @property
    def username(self) -> str:
        return self["username"]
    
    @property
    def roles(self) -> List[str]:
        return self.get("roles", [])
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles
    
    def has_any_role(self, *roles: str) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    FastAPI dependency to get current authenticated user from JWT token.
    
    Usage:
        @app.get("/profile")
        def get_profile(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    
    Raises:
        HTTPException: 401 if token is invalid or missing required claims
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Extract user information (compatible with auth-service token structure)
        user_id = payload.get("id") or payload.get("user_id") or payload.get("sub")
        email = payload.get("email")
        username = payload.get("username") or (email.split("@")[0] if email else "unknown")
        roles = payload.get("roles", [])
        
        # Validate required fields
        if not user_id:
            logger.warning("JWT missing user identifier", metadata={"token_payload": payload})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials: missing user identifier"
            )
        
        # Create user object
        user = User(
            user_id=user_id,
            email=email,
            username=username,
            roles=roles
        )
        
        logger.debug(f"User authenticated: {user_id}", metadata={"roles": roles})
        return user
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    FastAPI dependency for optional authentication.
    Returns User if valid token present, None otherwise.
    
    Usage:
        @app.get("/products")
        def list_products(user: Optional[User] = Depends(get_optional_user)):
            if user:
                # Return personalized results
                return {"products": [], "user": user.user_id}
            # Return public results
            return {"products": []}
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        user_id = payload.get("id") or payload.get("user_id") or payload.get("sub")
        if not user_id:
            return None
        
        email = payload.get("email")
        username = payload.get("username") or (email.split("@")[0] if email else "unknown")
        roles = payload.get("roles", [])
        
        return User(
            user_id=user_id,
            email=email,
            username=username,
            roles=roles
        )
    except JWTError:
        logger.debug("Optional auth: Invalid token provided")
        return None
    except Exception as e:
        logger.warning(f"Optional auth error: {str(e)}")
        return None


def require_roles(*required_roles: str) -> Callable[[User], User]:
    """
    Factory function to create a FastAPI dependency that requires specific roles.
    
    Usage:
        @app.get("/dashboard")
        def dashboard(user: User = Depends(require_roles("admin", "manager"))):
            return {"message": "Welcome to dashboard"}
    
    Args:
        *required_roles: One or more role names (user must have at least one)
    
    Returns:
        FastAPI dependency function
    """
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_any_role(*required_roles):
            logger.warning(
                f"Authorization failed: User {current_user.user_id} lacks required roles",
                metadata={
                    "required_roles": required_roles,
                    "user_roles": current_user.roles
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        
        logger.debug(
            f"Authorization successful: User {current_user.user_id}",
            metadata={"roles": current_user.roles}
        )
        return current_user
    
    return role_dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to require admin role.
    
    Usage:
        @app.post("/admin/products")
        def create_product(user: User = Depends(require_admin)):
            return {"message": "Product created"}
    """
    if not current_user.has_role("admin"):
        logger.warning(
            f"Admin access denied for user {current_user.user_id}",
            metadata={"roles": current_user.roles}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    logger.debug(f"Admin access granted for user {current_user.user_id}")
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to require customer or admin role.
    Admins can access customer endpoints.
    
    Usage:
        @app.post("/orders")
        def create_order(user: User = Depends(require_customer)):
            return {"order_id": "123"}
    """
    if not current_user.has_any_role("customer", "admin"):
        logger.warning(
            f"Customer access denied for user {current_user.user_id}",
            metadata={"roles": current_user.roles}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer or admin role required"
        )
    
    return current_user


# Service-layer helper functions (non-FastAPI dependencies)

def verify_admin_access(user: Optional[User]) -> None:
    """
    Service-layer helper to verify admin access.
    Use in business logic when you already have the user object.
    
    Usage:
        def delete_product(product_id: str, user: User):
            verify_admin_access(user)
            # Proceed with deletion
    
    Raises:
        HTTPException: 403 if user is not admin
    """
    if not user or not user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )


def verify_user_or_admin(user: Optional[User], target_user_id: str) -> None:
    """
    Service-layer helper to verify user is accessing their own data or is admin.
    
    Usage:
        def get_user_orders(user_id: str, user: User):
            verify_user_or_admin(user, user_id)
            # Fetch orders
    
    Raises:
        HTTPException: 403 if user is not the target user and not admin
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if user.user_id != target_user_id and not user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Can only access own resources"
        )
