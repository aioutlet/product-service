"""
Authentication dependencies for FastAPI
Provides JWT token validation and user extraction
"""

from typing import Optional
import jwt
from fastapi import Header, HTTPException, status

from app.core.config import config
from app.core.logger import logger
from app.models.user import User
from app.services.dapr_secret_manager import get_jwt_config

# Cache JWT config to avoid repeated Dapr calls
_jwt_config_cache = None


async def get_cached_jwt_config():
    """Get JWT config with caching"""
    global _jwt_config_cache
    if _jwt_config_cache is None:
        _jwt_config_cache = await get_jwt_config()
    return _jwt_config_cache


class AuthError(Exception):
    """Custom authentication error"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def decode_jwt(token: str) -> dict:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthError: If token is invalid or expired
    """
    try:
        jwt_config = await get_cached_jwt_config()
        payload = jwt.decode(
            token,
            jwt_config['secret'],
            algorithms=[jwt_config['algorithm']]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise AuthError("Invalid token", status.HTTP_401_UNAUTHORIZED)


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Dependency to extract and validate current user from JWT token.
    Raises 401 if authentication fails.
    
    Usage:
        @router.post("/")
        async def create_item(user: User = Depends(get_current_user)):
            # user is authenticated
            pass
    """
    if not authorization:
        logger.warning("Authentication required: No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Decode token
        payload = await decode_jwt(token)
        
        # Extract user information (compatible with auth-service token structure)
        user_id = payload.get("id") or payload.get("user_id") or payload.get("sub")
        email = payload.get("email")
        roles = payload.get("roles", [])
        
        if not user_id:
            logger.warning("Invalid token: Missing user ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: Missing user identifier",
            )
        
        user = User(id=user_id, email=email, roles=roles)
        logger.debug(f"Authentication successful for user: {user_id}")
        
        return user
        
    except AuthError as e:
        logger.warning(f"Authentication failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error",
        )


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns User if valid token provided, None otherwise.
    
    Usage:
        @router.get("/")
        async def list_items(user: Optional[User] = Depends(get_current_user_optional)):
            # user may be None
            pass
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        # Invalid token, but optional auth so return None
        return None


async def require_admin(user: User = Header(..., alias="user")) -> User:
    """
    Dependency to require admin role.
    Must be used with get_current_user.
    
    Usage:
        @router.delete("/{id}")
        async def delete_item(
            user: User = Depends(get_current_user),
            _: User = Depends(require_admin)
        ):
            # user is authenticated and has admin role
            pass
    """
    if not user.is_admin():
        logger.warning(f"Admin access denied for user: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
