import os

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.shared.core.errors import ErrorResponse
from src.shared.core.logger import logger

# Example secret and algorithm; in production, use env vars and secure config
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

security = HTTPBearer()

HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403


def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("id") or payload.get("user_id") or payload.get("sub")
        username = payload.get("username") or payload.get("email", "").split("@")[0]
        roles = payload.get("roles")
        if roles is None:
            roles = ["user"]
        if not user_id:
            logger.warning(
                "Invalid authentication credentials: missing user_id"
            )
            raise ErrorResponse(
                "Invalid authentication credentials", status_code=HTTP_401_UNAUTHORIZED
            )
        return {"user_id": user_id, "username": username, "roles": roles}
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise ErrorResponse(
            "Invalid authentication credentials", status_code=HTTP_401_UNAUTHORIZED
        )


def require_admin(user=Depends(get_current_user)):
    """
    FastAPI dependency for admin-only endpoints. Use as a dependency in route functions.
    """
    if "admin" not in user["roles"]:
        logger.warning(f"Admin privileges required. User: {user}")
        raise ErrorResponse("Admin privileges required", status_code=HTTP_403_FORBIDDEN)
    return user


def require_admin_user(acting_user):
    """
    Service-layer utility for admin-only logic.
    Use when you already have the user object.
    """
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse(
            "Only admin users can perform this action.", status_code=HTTP_403_FORBIDDEN
        )
