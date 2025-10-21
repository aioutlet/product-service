# FastAPI Authentication Migration

## Overview

Migrated product-service from improper authentication implementation to proper FastAPI standards following Python/FastAPI conventions.

## Problem

The previous implementation (`src/shared/core/auth.py`) violated FastAPI best practices:

1. **Wrong location**: Auth logic in `core/` instead of dedicated security package
2. **Mixed patterns**: Combined Node.js-style middleware with FastAPI dependencies
3. **Wrong error handling**: Used custom `ErrorResponse` instead of FastAPI's `HTTPException`
4. **No type safety**: Used plain dicts instead of typed User objects
5. **No separation**: Mixed route dependencies with service-layer helpers

## Solution

Created proper FastAPI security implementation in `src/shared/security/`:

### New Structure

```
src/shared/security/
├── dependencies.py    # FastAPI security dependencies
└── __init__.py       # Package exports
```

### Key Components

#### 1. User Class (Type-Safe)

```python
class User(dict):
    @property
    def user_id(self) -> str:
        return self["user_id"]

    @property
    def roles(self) -> List[str]:
        return self.get("roles", [])

    def has_role(self, role: str) -> bool:
        return role in self.roles
```

#### 2. Authentication Dependencies

- **`get_current_user(credentials=Depends(HTTPBearer()))`**: Main auth dependency
  - Decodes JWT token
  - Returns typed `User` object
  - Raises `HTTPException` on failure
- **`get_optional_user(credentials=Depends(HTTPBearer(auto_error=False)))`**: Optional auth
  - For public endpoints that benefit from user context
  - Returns `User` or `None`

#### 3. Authorization Dependencies

- **`require_admin(current_user=Depends(get_current_user))`**: Admin-only routes
- **`require_customer(current_user=Depends(get_current_user))`**: Customer or admin
- **`require_roles(*roles)`**: Factory function for custom role requirements

#### 4. Service-Layer Helpers

- **`verify_admin_access(user: User)`**: Check admin role in business logic
- **`verify_user_or_admin(user: User, target_user_id: str)`**: Check ownership or admin

## Migration Details

### Files Created

1. `src/shared/security/dependencies.py` - Complete FastAPI security implementation (280+ lines)
2. `src/shared/security/__init__.py` - Package exports
3. `FASTAPI_AUTH_MIGRATION.md` - This documentation

### Files Modified

1. **`src/api/routers/bulk_router.py`**

   - Changed import: `from src.shared.security import User, require_admin`
   - Updated function signatures: `user: User = Depends(require_admin)`
   - Changed property access: `user.user_id` instead of `user["user_id"]`

2. **`src/api/routers/import_export_router.py`**

   - Similar changes as bulk_router.py
   - Added "Requires admin role" to docstrings

3. **`src/api/routers/product_router.py`**

   - Updated all authenticated endpoints
   - Changed to use `User` type annotation
   - Import includes: `User, get_current_user, get_optional_user, require_admin`

4. **`src/api/routers/review_router.py`**

   - Updated all authenticated endpoints
   - Changed property access: `user.user_id` instead of `user["user_id"]`

5. **`src/api/controllers/product_controller.py`**
   - Replaced `require_admin_user()` with `verify_admin_access()` (service-layer helper)
   - Updated all user property access to use User class properties
   - Functions: `create_product`, `update_product`, `delete_product`, `reactivate_product`

### Files Removed

1. `src/shared/core/auth.py` - Old implementation that violated FastAPI standards

## FastAPI Best Practices Applied

### 1. Dependency Injection Pattern

```python
# ✅ CORRECT (FastAPI way)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    user: User = Depends(require_admin)  # Dependency injection
):
    pass

# ❌ WRONG (Traditional middleware approach)
@require_admin
async def update_product(...):
    pass
```

### 2. HTTPBearer Security Scheme

```python
# ✅ CORRECT
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    # Validate JWT...
```

### 3. Proper Error Handling

```python
# ✅ CORRECT (FastAPI)
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"}
)

# ❌ WRONG (Custom error response)
raise ErrorResponse("Unauthorized", status_code=401)
```

### 4. Type Safety

```python
# ✅ CORRECT (Typed User object)
class User(dict):
    @property
    def user_id(self) -> str:
        return self["user_id"]

async def endpoint(user: User = Depends(get_current_user)):
    user_id = user.user_id  # Type-safe property access

# ❌ WRONG (Plain dict)
async def endpoint(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]  # No type safety
```

### 5. Separation of Concerns

```python
# Route Dependencies (in routers)
async def create_product(user: User = Depends(require_admin)):
    pass

# Service-Layer Helpers (in controllers/services)
async def create_product_logic(user: User):
    verify_admin_access(user)  # Business logic validation
```

## JWT Token Structure

```json
{
  "id": "user123",
  "email": "user@example.com",
  "roles": ["customer", "admin"],
  "iat": 1234567890,
  "exp": 1234567900
}
```

## Role Hierarchy

- **customer**: Basic user role
- **admin**: All customer permissions + management capabilities
- **superadmin**: System configuration and all admin capabilities

## Usage Examples

### Admin-Only Endpoint

```python
@router.post("/products")
async def create_product(
    product: ProductCreate,
    user: User = Depends(require_admin)
):
    # Only admins can access this endpoint
    return await controller.create_product(product, user)
```

### Optional Authentication

```python
@router.get("/products")
async def list_products(
    user: User = Depends(get_optional_user)
):
    # Works for both authenticated and anonymous users
    # user will be None for anonymous requests
    pass
```

### Custom Role Requirements

```python
@router.post("/special")
async def special_endpoint(
    user: User = Depends(require_roles("admin", "moderator"))
):
    # Only admins or moderators can access
    pass
```

### Service-Layer Authorization

```python
async def update_product(product_id: str, user: User):
    # Check admin role in business logic
    verify_admin_access(user)

    # Or check ownership/admin
    verify_user_or_admin(user, product.created_by)
```

## Testing

To test the new authentication:

1. **Valid JWT Token**:

   ```bash
   curl -H "Authorization: Bearer <valid-jwt-token>" \
        http://localhost:8003/api/v1/products
   ```

2. **Admin Endpoint**:

   ```bash
   curl -X POST \
        -H "Authorization: Bearer <admin-jwt-token>" \
        -H "Content-Type: application/json" \
        -d '{"name":"Product","price":99.99}' \
        http://localhost:8003/api/v1/products
   ```

3. **Invalid Token** (should get 401):

   ```bash
   curl -H "Authorization: Bearer invalid-token" \
        http://localhost:8003/api/v1/products
   ```

4. **Customer accessing admin endpoint** (should get 403):
   ```bash
   curl -X POST \
        -H "Authorization: Bearer <customer-jwt-token>" \
        -H "Content-Type: application/json" \
        -d '{"name":"Product","price":99.99}' \
        http://localhost:8003/api/v1/products
   ```

## Benefits

1. **Standards Compliance**: Follows FastAPI documentation and Python conventions
2. **Type Safety**: IDE autocomplete and type checking with User class
3. **Better Error Handling**: Proper HTTP status codes and FastAPI exception handling
4. **Maintainability**: Clear separation between route dependencies and business logic
5. **Reusability**: Easy to add new role requirements with factory functions
6. **Documentation**: FastAPI auto-generates OpenAPI docs with security schemes

## Environment Variables Required

```bash
JWT_SECRET=your-secret-key-here  # Must match across all services
```

## Status Codes

- **401 Unauthorized**: Invalid or missing JWT token
- **403 Forbidden**: Valid token but insufficient permissions (wrong role)

## Next Steps

1. Test all endpoints with valid/invalid tokens
2. Consider adding similar pattern to other Python services (inventory-service)
3. Update API documentation with security requirements
4. Add unit tests for security dependencies
