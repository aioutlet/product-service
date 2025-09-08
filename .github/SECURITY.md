# Security Policy

## Overview

The Product Service is a high-performance Python FastAPI microservice responsible for product catalog management, search functionality, and product data operations within the AIOutlet platform. It handles product information, pricing data, and catalog management across the e-commerce ecosystem.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Features

### FastAPI Security Framework

- **FastAPI Security**: Built-in security utilities and OAuth2 support
- **Pydantic Validation**: Comprehensive input validation and serialization
- **JWT Authentication**: Secure token-based authentication with python-jose
- **Rate Limiting**: SlowAPI integration for request rate limiting

### Database Security

- **Motor/PyMongo**: Secure asynchronous MongoDB operations
- **Connection Security**: Encrypted MongoDB connections
- **Query Security**: NoSQL injection prevention
- **Index Security**: Secure database indexing strategies

### API Security

- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Sanitization**: Comprehensive data validation and cleaning
- **Response Filtering**: Secure data exposure controls
- **Upload Security**: Secure file upload handling for product images

### Performance Security

- **Async Operations**: Non-blocking secure operations
- **Connection Pooling**: Secure database connection management
- **Caching Security**: Redis integration with secure caching
- **Search Security**: Secure product search and filtering

### Monitoring & Observability

- **OpenTelemetry**: Distributed tracing with security context
- **Structured Logging**: Security-focused logging with sensitive data protection
- **Health Checks**: Comprehensive service health monitoring
- **Metrics Collection**: Secure performance metrics gathering

## Security Best Practices

### For Developers

1. **Environment Configuration**: Secure FastAPI application setup

   ```python
   # settings.py - Secure configuration management
   from pydantic import BaseSettings, Field
   from typing import List, Optional
   import os

   class Settings(BaseSettings):
       # Database Security
       mongodb_url: str = Field(..., env="MONGODB_URL")
       mongodb_database: str = Field("product_service", env="MONGODB_DATABASE")
       mongodb_ssl: bool = Field(True, env="MONGODB_SSL")

       # JWT Security
       jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
       jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
       jwt_expire_minutes: int = Field(60, env="JWT_EXPIRE_MINUTES")

       # API Security
       cors_origins: List[str] = Field(
           ["https://app.aioutlet.com"],
           env="CORS_ORIGINS"
       )
       max_request_size: int = Field(16777216, env="MAX_REQUEST_SIZE")  # 16MB

       # Rate Limiting
       rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
       rate_limit_period: int = Field(60, env="RATE_LIMIT_PERIOD")

       # Security Headers
       enable_security_headers: bool = Field(True, env="ENABLE_SECURITY_HEADERS")

       class Config:
           env_file = ".env"
           case_sensitive = False

   settings = Settings()
   ```

2. **Input Validation**: Comprehensive Pydantic models

   ```python
   from pydantic import BaseModel, Field, validator, HttpUrl
   from typing import Optional, List, Decimal
   from datetime import datetime
   import re

   class ProductCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=200)
       description: str = Field(..., min_length=1, max_length=5000)
       price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
       category_id: str = Field(..., regex="^[a-fA-F0-9]{24}$")
       sku: str = Field(..., min_length=1, max_length=50)
       brand: Optional[str] = Field(None, max_length=100)
       tags: List[str] = Field(default_factory=list, max_items=20)
       images: List[HttpUrl] = Field(default_factory=list, max_items=10)

       @validator('name', 'description')
       def sanitize_text(cls, v):
           # Remove potential XSS content
           return re.sub(r'<[^>]*>', '', v).strip()

       @validator('sku')
       def validate_sku(cls, v):
           # Ensure SKU contains only alphanumeric and safe characters
           if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
               raise ValueError('SKU contains invalid characters')
           return v.upper()

       @validator('tags')
       def validate_tags(cls, v):
           # Sanitize and validate tags
           return [re.sub(r'[<>"]', '', tag).strip() for tag in v if tag.strip()]

   class ProductFilter(BaseModel):
       category_id: Optional[str] = Field(None, regex="^[a-fA-F0-9]{24}$")
       min_price: Optional[Decimal] = Field(None, ge=0)
       max_price: Optional[Decimal] = Field(None, ge=0)
       brand: Optional[str] = Field(None, max_length=100)
       search: Optional[str] = Field(None, max_length=200)
       tags: Optional[List[str]] = Field(None, max_items=10)

       @validator('search')
       def sanitize_search(cls, v):
           if v:
               # Sanitize search query
               return re.sub(r'[<>"\';]', '', v).strip()
           return v
   ```

3. **Database Security**: Secure MongoDB operations

   ```python
   from motor.motor_asyncio import AsyncIOMotorClient
   from pymongo.errors import PyMongoError
   from bson import ObjectId
   from typing import Optional, List, Dict, Any
   import logging

   class ProductRepository:
       def __init__(self, database):
           self.collection = database.products
           self.collection.create_index([("sku", 1)], unique=True)
           self.collection.create_index([("name", "text"), ("description", "text")])

       async def create_product(self, product_data: dict) -> str:
           try:
               # Sanitize and validate data before insertion
               sanitized_data = self._sanitize_product_data(product_data)

               result = await self.collection.insert_one(sanitized_data)
               return str(result.inserted_id)
           except PyMongoError as e:
               logging.error(f"Database error creating product: {e}")
               raise ValueError("Failed to create product")

       async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
           try:
               # Validate ObjectId format
               if not ObjectId.is_valid(product_id):
                   return None

               product = await self.collection.find_one({"_id": ObjectId(product_id)})
               if product:
                   product["_id"] = str(product["_id"])
               return product
           except PyMongoError as e:
               logging.error(f"Database error retrieving product: {e}")
               return None

       async def search_products(self, filters: dict, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
           try:
               # Build secure query with proper validation
               query = self._build_secure_query(filters)

               # Limit results to prevent performance issues
               cursor = self.collection.find(query).skip(skip).limit(min(limit, 100))
               products = await cursor.to_list(length=None)

               # Convert ObjectId to string
               for product in products:
                   product["_id"] = str(product["_id"])

               return products
           except PyMongoError as e:
               logging.error(f"Database error searching products: {e}")
               return []

       def _sanitize_product_data(self, data: dict) -> dict:
           # Remove any potentially dangerous fields
           safe_fields = [
               "name", "description", "price", "category_id",
               "sku", "brand", "tags", "images", "created_at", "updated_at"
           ]
           return {k: v for k, v in data.items() if k in safe_fields}

       def _build_secure_query(self, filters: dict) -> dict:
           query = {}

           if filters.get("category_id"):
               if ObjectId.is_valid(filters["category_id"]):
                   query["category_id"] = ObjectId(filters["category_id"])

           if filters.get("min_price") is not None:
               query.setdefault("price", {})["$gte"] = float(filters["min_price"])

           if filters.get("max_price") is not None:
               query.setdefault("price", {})["$lte"] = float(filters["max_price"])

           if filters.get("brand"):
               # Case-insensitive brand search
               query["brand"] = {"$regex": f"^{re.escape(filters['brand'])}$", "$options": "i"}

           if filters.get("search"):
               # Text search with proper escaping
               query["$text"] = {"$search": filters["search"]}

           if filters.get("tags"):
               query["tags"] = {"$in": filters["tags"]}

           return query
   ```

4. **Authentication and Authorization**: Secure API access

   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   from jose import JWTError, jwt
   from datetime import datetime, timedelta
   import logging

   security = HTTPBearer()

   class AuthenticationService:
       def __init__(self, settings):
           self.secret_key = settings.jwt_secret_key
           self.algorithm = settings.jwt_algorithm
           self.expire_minutes = settings.jwt_expire_minutes

       def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
           try:
               payload = jwt.decode(
                   credentials.credentials,
                   self.secret_key,
                   algorithms=[self.algorithm]
               )

               # Verify token expiration
               exp = payload.get("exp")
               if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
                   raise HTTPException(
                       status_code=status.HTTP_401_UNAUTHORIZED,
                       detail="Token has expired"
                   )

               # Extract user information
               user_id = payload.get("sub")
               roles = payload.get("roles", [])

               if user_id is None:
                   raise HTTPException(
                       status_code=status.HTTP_401_UNAUTHORIZED,
                       detail="Invalid token"
                   )

               return {"user_id": user_id, "roles": roles}

           except JWTError as e:
               logging.warning(f"JWT validation error: {e}")
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Invalid token"
               )

       def require_role(self, required_role: str):
           def role_checker(current_user: dict = Depends(self.verify_token)):
               if required_role not in current_user.get("roles", []):
                   raise HTTPException(
                       status_code=status.HTTP_403_FORBIDDEN,
                       detail="Insufficient permissions"
                   )
               return current_user
           return role_checker
   ```

### For Deployment

1. **Application Security**:

   - Deploy with Uvicorn in production mode
   - Configure proper security headers
   - Enable HTTPS with valid certificates
   - Implement request size limits

2. **Database Security**:

   - Enable MongoDB authentication and SSL
   - Configure proper database user permissions
   - Implement connection limits and timeouts
   - Regular security updates

3. **Container Security**:
   - Use minimal Python base images
   - Scan images for vulnerabilities
   - Implement runtime security monitoring
   - Secure container orchestration

## Data Handling

### Sensitive Data Categories

1. **Product Information**:

   - Product pricing and cost data
   - Proprietary product descriptions
   - Supplier and vendor information
   - Inventory and stock data

2. **Business Data**:

   - Product performance metrics
   - Pricing strategies and margins
   - Category and taxonomy data
   - Search and recommendation algorithms

3. **Customer Data**:
   - Product views and interactions
   - Search queries and patterns
   - Wishlist and preference data
   - Product reviews and ratings

### Data Protection Measures

- **Input Sanitization**: Comprehensive XSS and injection prevention
- **Database Security**: Encrypted MongoDB connections and authentication
- **API Security**: Rate limiting and request validation
- **Data Masking**: Sensitive information masking in logs

### Data Retention

- Product catalog data: Permanent (until product retirement)
- Product performance metrics: 2 years
- Customer interaction data: 1 year (anonymized)
- Search analytics: 6 months (aggregated)

## Vulnerability Reporting

### Reporting Security Issues

Product service vulnerabilities can affect catalog integrity:

1. **Do NOT** open a public issue
2. **Do NOT** attempt to modify product data
3. **Email** our security team at: <security@aioutlet.com>

### Critical Security Areas

- Product data manipulation
- Price tampering vulnerabilities
- Search injection attacks
- Unauthorized catalog access
- Performance-based DoS attacks

### Response Timeline

- **8 hours**: Critical product manipulation issues
- **24 hours**: High severity data exposure
- **72 hours**: Medium severity issues
- **7 days**: Low severity issues

### Severity Classification

| Severity | Description                                | Examples                              |
| -------- | ------------------------------------------ | ------------------------------------- |
| Critical | Product manipulation, price tampering      | Catalog corruption, pricing attacks   |
| High     | Data injection, unauthorized access        | NoSQL injection, privilege escalation |
| Medium   | Information disclosure, performance issues | Data leakage, DoS attacks             |
| Low      | Minor API issues, logging problems         | Response formatting, metrics accuracy |

## Security Testing

### Product Service Testing

Regular security assessments should include:

- Product data validation and sanitization testing
- NoSQL injection vulnerability testing
- Search functionality security testing
- Rate limiting effectiveness verification
- Authentication and authorization testing

### Automated Security Testing

- Unit tests for input validation and business logic
- Integration tests for secure database operations
- Load testing for high-volume product operations
- Security tests for API endpoints

## Security Configuration

### Required Environment Variables

```bash
# Database Security
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/productdb?ssl=true
MONGODB_DATABASE=product_service
MONGODB_SSL=true
MONGODB_MAX_POOL_SIZE=50

# JWT Security
JWT_SECRET_KEY=your-256-bit-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# API Security
CORS_ORIGINS=https://app.aioutlet.com,https://admin.aioutlet.com
MAX_REQUEST_SIZE=16777216
ENABLE_SECURITY_HEADERS=true

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
RATE_LIMIT_STORAGE=redis://localhost:6379

# Search Security
MAX_SEARCH_RESULTS=100
SEARCH_TIMEOUT=5
ENABLE_SEARCH_ANALYTICS=true

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces
OTEL_SERVICE_NAME=product-service
OTEL_RESOURCE_ATTRIBUTES=service.name=product-service,service.version=1.0.0
```

### Python Security Configuration

```python
# main.py - Secure FastAPI application setup
from fastapi import FastAPI, middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Product Service API",
    description="Secure product catalog management",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)

    if settings.enable_security_headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response
```

## Compliance

The Product Service adheres to:

- **E-commerce Security**: Industry-standard catalog security practices
- **GDPR**: Customer data protection in product interactions
- **CCPA**: California consumer privacy for product data
- **PCI DSS**: Payment-related product information security
- **Data Protection**: Privacy-compliant analytics and tracking

## Performance & Security

### High-Performance Security

- **Async Operations**: Non-blocking secure database operations
- **Connection Pooling**: Efficient secure MongoDB connections
- **Caching Security**: Redis-based secure caching strategies
- **Search Optimization**: Secure and efficient product search

## Incident Response

### Product Service Security Incidents

1. **Product Data Tampering**: Immediate catalog freeze and integrity check
2. **Price Manipulation**: Price validation and rollback procedures
3. **Search Injection**: Query sanitization and security hardening
4. **Service Compromise**: Service isolation and security assessment

### Recovery Procedures

- Product catalog restoration from secure backups
- Data integrity verification and correction
- Search index rebuilding with security validation
- Performance optimization after security updates

## Contact

For security-related questions or concerns:

- **Email**: <security@aioutlet.com>
- **Emergency**: Include "URGENT PRODUCT SECURITY" in subject line
- **Catalog Issues**: Copy <catalog@aioutlet.com>

---

**Last Updated**: September 8, 2025  
**Next Review**: December 8, 2025  
**Version**: 1.0.0
