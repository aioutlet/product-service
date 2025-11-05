# Product Service - Technical Architecture

> **Service**: Product Service  
> **Version**: 1.0  
> **Last Updated**: November 3, 2025  
> **Status**: Active

## Table of Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Architecture Layers](#architecture-layers)
- [Code Structure](#code-structure)
- [Design Patterns](#design-patterns)
- [Data Layer](#data-layer)
- [Event-Driven Architecture](#event-driven-architecture)
- [API Layer](#api-layer)
- [Error Handling](#error-handling)
- [Caching Strategy](#caching-strategy)
- [Testing Strategy](#testing-strategy)
- [Performance Optimization](#performance-optimization)

---

## Overview

Product Service is the **source of truth** for product catalog data in the AIOutlet platform. It follows a **layered architecture** pattern with clear separation of concerns and implements **event-driven integration** using Dapr Pub/Sub for asynchronous communication.

### Service Responsibilities

1. **Product Management**: CRUD operations for products and variations
2. **Product Discovery**: Search, filtering, pagination
3. **Event Publishing**: Notify other services of product changes
4. **Event Consumption**: Sync denormalized data from other services (reviews, inventory, analytics)
5. **Administrative Operations**: Bulk imports, badge management, statistics

### Architecture Principles

- **Layered Architecture**: Clear separation between API, business logic, and data access
- **Dependency Injection**: Loose coupling, testability
- **Repository Pattern**: Abstract data access layer
- **Event Sourcing (Partial)**: Publish domain events for all state changes
- **CQRS-Lite**: Separate read/write operations where beneficial
- **Eventual Consistency**: Accept stale data for performance (5-10s SLA)

---

## Technology Stack

### Runtime & Language

- **Python**: v3.11+ or v3.12
- **pip**: Package management
- **Virtual Environment**: venv or Poetry for dependency isolation

### Web Framework

- **FastAPI**: Modern async web framework
- **Uvicorn**: ASGI server (production-ready)
- **Starlette**: ASGI framework (FastAPI foundation)
- **Pydantic**: Data validation and serialization

### Database

- **MongoDB**: v7.x (document database)
- **Motor**: Async MongoDB driver for Python
- **PyMongo**: Alternative sync driver
- **Pydantic**: Schema validation and serialization
  - Type hints for validation
  - Automatic API documentation
  - JSON serialization

### Event System

- **Dapr SDK for Python**: Event pub/sub abstraction
- **RabbitMQ**: Message broker (behind Dapr)
- **Topics**: `product.events`, `review.events`, `inventory.events`, `analytics.events`

### Validation & Serialization

- **Pydantic**: Request/response models with validation
- **FastAPI**: Built-in OpenAPI documentation
- **Python type hints**: Static type checking

### Logging & Monitoring

- **Python logging**: Structured JSON logging
- **Loguru**: Modern logging alternative
- **Prometheus Client**: Metrics export
- **Correlation ID Middleware**: Request tracing

### Testing

- **Pytest**: Unit and integration testing
- **httpx**: Async HTTP client for testing
- **pytest-asyncio**: Async test support
- **Faker**: Test data generation
- **mongomock**: In-memory MongoDB for tests

### Development Tools

- **Black**: Code formatting
- **Flake8**: Code linting
- **mypy**: Static type checking
- **isort**: Import sorting
- **pre-commit**: Git hooks for code quality
- **uvicorn**: ASGI server with hot reload

---

## Architecture Layers

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (HTTP)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Routes   │  │ Middleware │  │Dependencies│            │
│  │ (FastAPI)  │  │(Auth, Log) │  │(Dependency │            │
│  │            │  │            │  │ Injection) │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼────────────────┼────────────────┼───────────────────┘
         │                │                │
         └────────────────┴────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────────┐
│                   Service Layer (Business Logic)              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Product Service│  │ Variation      │  │ Badge Service  │ │
│  │  (Domain Logic)│  │   Service      │  │                │ │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘ │
└───────────┼──────────────────────┼──────────────────┼─────────┘
            │                      │                  │
            └──────────────────────┴──────────────────┘
                                   │
┌───────────────────────────────────┼──────────────────────────┐
│                     Repository Layer (Data Access)           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐│
│  │Product Repo    │  │ Event Publisher│  │ Event Consumer ││
│  │  (Motor)       │  │  (Dapr)        │  │  (Dapr)        ││
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘│
└───────────┼──────────────────────┼──────────────────┼────────┘
            │                      │                  │
            ▼                      ▼                  ▼
      ┌──────────┐          ┌──────────┐      ┌──────────┐
      │ MongoDB  │          │ RabbitMQ │      │ RabbitMQ │
      │ (Primary)│          │(Publish) │      │(Consume) │
      └──────────┘          └──────────┘      └──────────┘
```

### Layer Responsibilities

#### 1. API Layer (`src/api/`, `src/middleware/`, `src/dependencies/`)

- **Routes**: Define FastAPI endpoint handlers with proper HTTP methods
- **Dependencies**: FastAPI dependency injection for auth, database, services
- **Middleware**: Authentication, authorization, logging, error handling, CORS

#### 2. Service Layer (`src/services/`)

- **Business Logic**: Product creation rules, validation, workflows
- **Domain Events**: Trigger event publishing on state changes
- **Orchestration**: Coordinate multiple repositories/external calls

#### 3. Repository Layer (`src/repositories/`)

- **Data Access**: CRUD operations on MongoDB using Motor (async)
- **Query Building**: Complex queries, aggregations, pagination
- **Transactions**: Multi-document operations (where needed)

#### 4. Event Layer (`src/events/`)

- **Event Publishers**: Publish domain events via Dapr
- **Event Consumers**: Subscribe and handle events from other services
- **Event Schemas**: Pydantic models for type-safe event payloads

---

## Code Structure

```
product-service/
├── src/                          # Main application package
│   ├── api/                      # FastAPI route handlers (endpoints)
│   │   ├── __init__.py
│   │   ├── products.py                # Product CRUD endpoints
│   │   ├── variations.py              # Variation endpoints
│   │   ├── search.py                  # Search/filter endpoints
│   │   ├── admin.py                   # Admin-only endpoints
│   │   └── health.py                  # Health check endpoints
│   │
│   ├── schemas/                  # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── product.py                 # ProductResponse, ProductListResponse
│   │   ├── requests.py                # CreateProductRequest, UpdateProductRequest
│   │   └── common.py                  # PaginationParams, ErrorResponse
│   │
│   ├── models/                   # Database models (MongoDB documents)
│   │   ├── __init__.py
│   │   ├── product.py                 # Product database model
│   │   └── variation.py               # Variation database model
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── product_service.py         # Product domain logic
│   │   ├── variation_service.py       # Variation logic
│   │   ├── badge_service.py           # Badge assignment logic
│   │   ├── search_service.py          # Search/filter logic
│   │   └── bulk_import_service.py     # Bulk operations
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py         # Generic CRUD operations
│   │   ├── product_repository.py      # Product-specific queries
│   │   └── query_builder.py           # Complex query helper
│   │
│   ├── events/                   # Event-driven architecture
│   │   ├── __init__.py
│   │   ├── publishers/
│   │   │   ├── __init__.py
│   │   │   ├── base_publisher.py      # Base Dapr publisher class
│   │   │   └── product_publisher.py   # Publish product events (Dapr)
│   │   ├── consumers/
│   │   │   ├── __init__.py
│   │   │   ├── review_consumer.py     # Consume review events
│   │   │   ├── inventory_consumer.py  # Consume inventory events
│   │   │   ├── analytics_consumer.py  # Consume analytics events
│   │   │   └── qa_consumer.py         # Consume Q&A events
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── product_events.py      # Product event models (CloudEvents)
│   │       ├── review_events.py       # Review event models
│   │       └── inventory_events.py    # Inventory event models
│   │
│   ├── dependencies/             # FastAPI dependency injection
│   │   ├── __init__.py
│   │   ├── auth.py                    # get_current_user, require_admin
│   │   ├── database.py                # get_database dependency
│   │   └── services.py                # get_product_service, etc.
│   │
│   ├── middleware/               # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── auth.py                    # JWT validation middleware
│   │   ├── correlation_id.py          # Request tracing (X-Correlation-ID)
│   │   ├── logging.py                 # Request/response logging
│   │   └── error_handler.py           # Global exception handler
│   │
│   ├── core/                     # Core configuration and setup
│   │   ├── __init__.py
│   │   ├── config.py                  # Settings (Pydantic BaseSettings)
│   │   ├── database.py                # MongoDB connection & session
│   │   ├── security.py                # JWT validation, password hashing
│   │   ├── logging.py                 # Structured logging configuration
│   │   └── events.py                  # Dapr client initialization
│   │
│   ├── validators/               # Custom validation logic
│   │   ├── __init__.py
│   │   ├── product_validators.py      # Product-specific validators
│   │   └── config_validator.py        # Environment config validation
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── errors.py                  # Custom exception classes
│   │   ├── pagination.py              # Pagination helpers
│   │   ├── correlation_id.py          # Correlation ID utilities
│   │   └── dependency_health_checker.py # Health check utilities
│   │
│   ├── __init__.py
│   └── main.py                   # FastAPI app setup & entry point
│
├── tests/
│   ├── __init__.py
│   ├── unit/                     # Unit tests (services, utils)
│   │   ├── __init__.py
│   │   ├── test_product_service.py
│   │   └── test_utils.py
│   ├── integration/              # Integration tests (API endpoints)
│   │   ├── __init__.py
│   │   └── test_product_api.py
│   ├── e2e/                      # End-to-end tests
│   │   ├── __init__.py
│   │   └── test_workflows.py
│   ├── fixtures/                 # Test data
│   │   ├── __init__.py
│   │   └── product_fixtures.py
│   └── conftest.py               # Pytest configuration & fixtures
│
├── docs/
│   ├── PRD.md                    # Product requirements
│   ├── ARCHITECTURE.md           # This document
│   └── API.md                    # API documentation (optional)
│
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local dev environment
├── .env.example                  # Environment variables template
├── pyproject.toml                # Dependencies (Poetry)
├── requirements.txt              # Dependencies (pip)
├── pytest.ini                    # Pytest configuration
├── .flake8                       # Flake8 linting configuration
├── mypy.ini                      # mypy type checking configuration
└── README.md                     # Service readme
```

---

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract database operations from business logic

**Implementation**:

```python
# Base Repository (shared CRUD)
from typing import Generic, TypeVar, Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(id)})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return await self.find_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0


# Product Repository (domain-specific)
from src.repositories.base_repository import BaseRepository

class ProductRepository(BaseRepository):
    async def find_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"sku": sku})

    async def search_products(self, filters: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        cursor = self.collection.find(filters).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_variations(self, parent_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"parentId": parent_id})
        return await cursor.to_list(length=None)
```

### 2. Service Layer Pattern

**Purpose**: Encapsulate business logic, orchestrate repositories

**Implementation**:

```python
from src.repositories.product_repository import ProductRepository
from src.events.publishers.product_publisher import ProductEventPublisher
from src.core.logging import logger
from src.utils.errors import DuplicateSkuError
from src.models.product import Product

class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        event_publisher: ProductEventPublisher
    ):
        self.product_repo = product_repo
        self.event_publisher = event_publisher

    async def create_product(self, data: dict) -> Product:
        # Business validation
        await self._validate_sku(data["sku"])

        # Create product
        product_data = await self.product_repo.create(data)
        product = Product(**product_data)

        # Publish domain event
        await self.event_publisher.publish_product_created(product)

        # Log operation
        logger.info(f"Product created", extra={
            "productId": str(product.id),
            "sku": product.sku
        })

        return product

    async def _validate_sku(self, sku: str) -> None:
        existing = await self.product_repo.find_by_sku(sku)
        if existing:
            raise DuplicateSkuError(f"SKU {sku} already exists")
```

### 3. Dependency Injection

**Purpose**: Loose coupling, testability

**Implementation**:

```python
# Using FastAPI's dependency injection
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.core.database import get_database

def get_product_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ProductRepository:
    return ProductRepository(db["products"])

def get_product_service(
    repo: ProductRepository = Depends(get_product_repository)
) -> ProductService:
    event_publisher = ProductEventPublisher()
    return ProductService(repo, event_publisher)

# Use in route handlers
from fastapi import APIRouter, Depends
from src.services.product_service import ProductService
from src.dependencies.services import get_product_service

router = APIRouter()

@router.post("/products", status_code=201)
async def create_product(
    data: CreateProductRequest,
    service: ProductService = Depends(get_product_service)
):
    product = await service.create_product(data.dict())
    return product
```

### 4. Middleware Chain

**Purpose**: Cross-cutting concerns (auth, logging, error handling)

**Implementation**:

```python
# Middleware applied at app level
from fastapi import FastAPI
from src.middleware.correlation_id import CorrelationIdMiddleware
from src.middleware.logging import LoggingMiddleware
from src.middleware.error_handler import ErrorHandlerMiddleware

app = FastAPI()

# Global middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Dependency-based middleware for routes
from src.dependencies.auth import get_current_user, require_admin

@router.post("/products", dependencies=[Depends(require_admin)])
async def create_product(
    data: CreateProductRequest,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service)
):
    product = await service.create_product(data.dict())
    return product
```

### 5. Event Publisher Pattern

**Purpose**: Decouple event publishing from business logic

**Implementation**:

```python
from dapr.clients import DaprClient
from uuid import uuid4
from datetime import datetime
from src.models.product import Product
from src.core.context import get_correlation_id

class ProductEventPublisher:
    def __init__(self):
        self.dapr_client = DaprClient()
        self.pubsub_name = "pubsub"
        self.topic_name = "product.events"

    async def publish_product_created(self, product: Product) -> None:
        event = {
            "eventType": "product.created",
            "eventId": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "correlationId": get_correlation_id(),
            "data": {
                "productId": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "price": product.price,
                "status": product.status,
            }
        }

        with self.dapr_client:
            self.dapr_client.publish_event(
                pubsub_name=self.pubsub_name,
                topic_name=self.topic_name,
                data=event
            )
```

---

## Data Layer

### MongoDB Schema Design

**Product Pydantic Model** (for validation and serialization):

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ReviewAggregates(BaseModel):
    averageRating: float = 0.0
    totalReviews: int = 0
    lastUpdated: Optional[datetime] = None


class AvailabilityStatus(BaseModel):
    isAvailable: bool = True
    stockLevel: Literal["in_stock", "low_stock", "out_of_stock"] = "in_stock"
    lastChecked: Optional[datetime] = None


class Product(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)
    status: Literal["active", "inactive", "draft"] = "active"
    variationType: Literal["standalone", "parent", "child"] = "standalone"
    parentId: Optional[str] = None

    # Denormalized data
    reviewAggregates: ReviewAggregates = Field(default_factory=ReviewAggregates)
    availabilityStatus: AvailabilityStatus = Field(default_factory=AvailabilityStatus)

    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Classic T-Shirt",
                "sku": "TS-BLK-001",
                "price": 29.99,
                "status": "active",
                "variationType": "parent"
            }
        }
```

**MongoDB Indexes** (created at startup):

```python
from motor.motor_asyncio import AsyncIOMotorDatabase

async def create_indexes(db: AsyncIOMotorDatabase):
    collection = db["products"]

    # Single field indexes
    await collection.create_index("name")
    await collection.create_index("sku", unique=True)
    await collection.create_index("status")
    await collection.create_index("parentId", sparse=True)

    # Compound indexes
    await collection.create_index([("status", 1), ("price", 1)])
    await collection.create_index([("taxonomy.category", 1), ("status", 1)])

    # Text index for full-text search
    await collection.create_index([("name", "text"), ("description", "text")])
```

### Query Patterns

**Simple Queries**:

```python
# Find by ID
from bson import ObjectId

product = await collection.find_one({"_id": ObjectId(id)})

# Find by SKU
product = await collection.find_one({"sku": "TS-BLK-001"})

# Find all active products
cursor = collection.find({"status": "active"}).limit(20)
products = await cursor.to_list(length=20)
```

**Complex Queries**:

```python
# Search with filters and pagination
cursor = collection.find({
    "status": "active",
    "taxonomy.category": "Clothing",
    "price": {"$gte": 20, "$lte": 50}
}).sort("createdAt", -1).skip(page * limit).limit(limit)

products = await cursor.to_list(length=limit)

# Aggregation for statistics
pipeline = [
    {"$match": {"status": "active"}},
    {
        "$group": {
            "_id": "$taxonomy.category",
            "count": {"$sum": 1},
            "avgPrice": {"$avg": "$price"},
            "minPrice": {"$min": "$price"},
            "maxPrice": {"$max": "$price"}
        }
    }
]

cursor = collection.aggregate(pipeline)
stats = await cursor.to_list(length=None)
```

**Variation Queries**:

```python
# Get all variations of a parent product
cursor = collection.find({"parentId": parent_id})
variations = await cursor.to_list(length=None)

# Get parent from child
child = await collection.find_one({"_id": ObjectId(child_id)})
if child and child.get("parentId"):
    parent = await collection.find_one({"_id": ObjectId(child["parentId"])})
```

---

## Event-Driven Architecture

### Event Publishing (Outbound)

**Dapr Pub/Sub Configuration**:

```python
# Initialize Dapr client
from dapr.clients import DaprClient
import os

class DaprClientSingleton:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = DaprClient()
        return cls._instance

    def get_client(self):
        return self._client

# Publish event
from uuid import uuid4
from datetime import datetime
from app.core.context import get_correlation_id

async def publish_product_created_event(product: dict) -> None:
    dapr_client = DaprClientSingleton().get_client()

    event = {
        "eventType": "product.created",
        "eventId": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "correlationId": get_correlation_id(),
        "data": {
            "productId": str(product["_id"]),
            "sku": product["sku"],
            "name": product["name"],
            "price": product["price"],
            "status": product["status"],
            "category": product.get("taxonomy", {}).get("category")
        }
    }

    with dapr_client:
        dapr_client.publish_event(
            pubsub_name="pubsub",  # Pub/sub component name (from dapr.yaml)
            topic_name="product.events",  # Topic name
            data=event
        )
```

**Published Events**:

1. `product.created` - New product created
2. `product.updated` - Product modified
3. `product.deleted` - Product soft-deleted
4. `product.price.changed` - Price updated
5. `product.back.in.stock` - Out-of-stock product back in stock
6. `product.badge.assigned` - Badge added to product
7. `product.badge.removed` - Badge removed from product

### Event Consumption (Inbound)

**Dapr Subscription Setup**:

```python
# FastAPI endpoints for Dapr subscriptions
from fastapi import FastAPI, Request
from src.services.product_service import ProductService

app = FastAPI()

# Dapr subscription endpoint
@app.get("/dapr/subscribe")
async def subscribe():
    return [
        {
            "pubsubname": "pubsub",
            "topic": "review.events",
            "route": "/events/review"
        },
        {
            "pubsubname": "pubsub",
            "topic": "inventory.events",
            "route": "/events/inventory"
        },
        {
            "pubsubname": "pubsub",
            "topic": "analytics.events",
            "route": "/events/analytics"
        }
    ]

# Handle review events
@app.post("/events/review")
async def handle_review_event(request: Request):
    event_data = await request.json()
    event = event_data.get("data", {})

    if event.get("eventType") in ["review.created", "review.updated"]:
        product_service = ProductService()
        await product_service.update_review_aggregates(
            event["data"]["productId"],
            event["data"]["aggregates"]
        )

    return {"status": "SUCCESS"}  # Acknowledge to Dapr
```

**Consumed Events**:

1. `review.created`, `review.updated`, `review.deleted` → Update review aggregates
2. `inventory.stock.updated`, `inventory.reserved`, `inventory.released` → Update availability status
3. `analytics.product.sales.updated` → Update sales metrics for badge automation
4. `product.question.created`, `product.answer.created` → Update Q&A counts

### Event Processing Strategy

**Idempotency**:

```python
# Use event ID to prevent duplicate processing
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

async def handle_review_event(event: dict, db: AsyncIOMotorDatabase) -> None:
    processed_events = db["processed_events"]
    event_id = event.get("eventId")

    # Check if already processed
    existing = await processed_events.find_one({"eventId": event_id})
    if existing:
        logger.info(f"Event already processed: {event_id}")
        return  # Skip duplicate

    # Process event
    product_service = ProductService()
    await product_service.update_review_aggregates(
        event["data"]["productId"],
        event["data"]["aggregates"]
    )

    # Mark as processed
    await processed_events.insert_one({
        "eventId": event_id,
        "processedAt": datetime.utcnow()
    })
```

**Retry Strategy**:

- Dapr automatically retries failed events (configurable)
- Max retries: 3
- Backoff: Exponential (1s, 2s, 4s)
- Dead Letter Queue: Failed events after max retries

---

### Service-to-Service Communication (Dapr Service Invocation)

Product Service can be called by other internal services using **Dapr Service Invocation** building block for synchronous request-response patterns.

#### Architecture Pattern

```
┌─────────────────┐                    ┌─────────────────┐
│  Order Service  │                    │ Product Service │
│  + Dapr Sidecar │                    │  + Dapr Sidecar │
└────────┬────────┘                    └────────▲────────┘
         │                                      │
         │ 1. Invoke product-service           │
         │    GET /products/{id}               │
         ▼                                      │
┌──────────────────────┐              ┌──────────────────────┐
│ Dapr Runtime (Order) │──── HTTP ───►│ Dapr Runtime (Prod)  │
│ Service Invocation   │              │ Service Invocation   │
└──────────────────────┘              └──────────────────────┘
         │                                      │
         │ 2. Service Discovery                 │ 3. Forward to App
         │    (find product-service)            │    localhost:8003
         │                                      │
         └──────────────────────────────────────┘
                    4. Return Response
```

#### Inbound Service Invocation (Product Service as Receiver)

**Callers**: order-service, cart-service, recommendation-service, etc.

**Endpoints exposed for service invocation**:

```python
# app/api/v1/products.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.product_service import ProductService

router = APIRouter()

# Called by order-service to validate products in order
@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get product details by ID.
    Used by other services for product validation and information.
    """
    product = await product_service.get_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"success": True, "data": product}

# Called by cart-service to check inventory
@router.post("/products/check-availability")
async def check_availability(
    product_ids: list[str],
    product_service: ProductService = Depends(get_product_service)
):
    """
    Check if products are available and active.
    Used by cart-service before adding items.
    """
    results = await product_service.check_bulk_availability(product_ids)
    return {"success": True, "data": results}
```

**Note**: No special code changes needed in product-service. Dapr handles the invocation transparently.

#### Outbound Service Invocation (Product Service as Caller)

**Future Use Case**: If product-service needs to call other services (not currently implemented)

```python
# Example: Call inventory-service to check stock (hypothetical)
from dapr.clients import DaprClient
import json

async def check_inventory_stock(product_id: str, quantity: int) -> dict:
    """Call inventory-service via Dapr service invocation."""
    try:
        with DaprClient() as dapr:
            response = dapr.invoke_method(
                app_id='inventory-service',  # Target service app-id
                method_name='inventory/check',  # Endpoint path
                data=json.dumps({
                    'productId': product_id,
                    'quantity': quantity
                }),
                http_verb='POST'
            )

            return json.loads(response.data)
    except Exception as e:
        logger.error(f"Failed to check inventory via Dapr: {e}")
        raise
```

#### Benefits of Dapr Service Invocation

1. **Service Discovery**: No need to hard-code URLs (e.g., `http://product-service:8003`)
2. **mTLS**: Automatic mutual TLS encryption between services
3. **Retries**: Built-in retry logic with exponential backoff
4. **Timeouts**: Configurable timeout handling
5. **Observability**: Distributed tracing via OpenTelemetry
6. **Resiliency**: Circuit breakers and bulkheads
7. **Load Balancing**: Automatic load distribution across instances

#### Configuration

**Dapr Sidecar**:

```yaml
# components/pubsub.yaml (already configured)
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: product-pubsub
spec:
  type: pubsub.rabbitmq
  # ...
```

**No additional configuration needed** for service invocation - it works out of the box with Dapr sidecars.

#### Service Invocation vs Pub/Sub

| Pattern                | Use Case                        | Example                                                  |
| ---------------------- | ------------------------------- | -------------------------------------------------------- |
| **Service Invocation** | Synchronous request-response    | order-service → product-service (GET /products/{id})     |
| **Pub/Sub**            | Asynchronous event notification | product-service → search-service (product.created event) |

**When to use Service Invocation**:

- Need immediate response
- Direct service dependency is acceptable
- CRUD operations (GET, POST, PUT, DELETE)
- Validation/authorization checks

**When to use Pub/Sub**:

- Fire-and-forget notifications
- Multiple consumers for same event
- Decoupled architecture
- Event-driven workflows

---

## API Layer

### REST Endpoints

**Product CRUD**:

```python
# Create product
POST /api/products
Authorization: Bearer <admin-jwt>
Body: { "name": "...", "sku": "...", "price": 29.99, ... }
Response: 201 Created

# Get product by ID
GET /api/products/{id}
Response: 200 OK

# Update product
PUT /api/products/{id}
Authorization: Bearer <admin-jwt>
Body: { "price": 39.99, "status": "active", ... }
Response: 200 OK

# Delete product (soft delete)
DELETE /api/products/{id}
Authorization: Bearer <admin-jwt>
Response: 204 No Content
```

**Search & Filter**:

```python
# Search products
GET /api/products?search=cotton&category=Clothing&minPrice=20&maxPrice=50&page=1&limit=20
Response: 200 OK { "products": [...], "pagination": {...} }

# Get variations
GET /api/products/{parent_id}/variations?page=1&limit=50
Response: 200 OK { "variations": [...] }
```

**Admin Operations**:

```python
# Get statistics
GET /api/admin/products/statistics
Authorization: Bearer <admin-jwt>
Response: 200 OK { "totalProducts": 150, "byCategory": {...}, ... }

# Bulk import
POST /api/admin/products/bulk/import
Authorization: Bearer <admin-jwt>
Body: { "products": [...] }
Response: 202 Accepted { "jobId": "job-123" }

# Check bulk import status
GET /api/admin/products/bulk/status/{job_id}
Authorization: Bearer <admin-jwt>
Response: 200 OK { "status": "processing", "progress": 45 }
```

### FastAPI Router Implementation

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from src.dependencies.auth import get_current_user, require_admin
from src.services.product_service import ProductService
from src.schemas.requests import CreateProductRequest, UpdateProductRequest
from src.schemas.product import ProductResponse

router = APIRouter(prefix="/api/products", tags=["products"])

@router.post("", status_code=201, response_model=ProductResponse, dependencies=[Depends(require_admin)])
async def create_product(
    data: CreateProductRequest,
    service: ProductService = Depends(get_product_service)
):
    product = await service.create_product(data.dict())
    return product

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    service: ProductService = Depends(get_product_service)
):
    product = await service.get_product_by_id(product_id)
    if not product:
        raise ProductNotFoundError(product_id)
    return product

@router.get("", response_model=List[ProductResponse])
async def search_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, alias="minPrice"),
    max_price: Optional[float] = Query(None, alias="maxPrice"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: ProductService = Depends(get_product_service)
):
    products = await service.search_products(
        filters={"search": search, "category": category, "minPrice": min_price, "maxPrice": max_price},
        page=page,
        limit=limit
    )
    return products
```

### Middleware Execution Order

```
1. CorrelationIdMiddleware     → Generate/propagate X-Correlation-ID
2. LoggingMiddleware (request) → Log incoming request
3. ErrorHandlerMiddleware      → Catch and format errors (outermost)
4. [Dependencies]              → JWT validation, RBAC check
5. [ROUTER FUNCTION]           → Execute business logic
6. LoggingMiddleware (response)→ Log response
```

---

## Error Handling

### Error Hierarchy

```python
# Base error class
from fastapi import HTTPException

class AppError(HTTPException):
    def __init__(self, message: str, status_code: int, error_code: str, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


# Domain-specific errors
class ProductNotFoundError(AppError):
    def __init__(self, product_id: str):
        super().__init__(
            message=f"Product with ID {product_id} not found",
            status_code=404,
            error_code="PRODUCT_NOT_FOUND"
        )


class DuplicateSkuError(AppError):
    def __init__(self, sku: str, existing_product_id: str = None):
        super().__init__(
            message=f"Product with SKU '{sku}' already exists",
            status_code=400,
            error_code="DUPLICATE_SKU",
            details={"sku": sku, "existingProductId": existing_product_id}
        )


class ValidationError(AppError):
    def __init__(self, fields: list):
        super().__init__(
            message="Validation failed",
            status_code=400,
            error_code="VALIDATION_ERROR",
            details={"fields": fields}
        )
```

### Global Error Handler

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.core.logging import logger
from src.core.context import get_correlation_id
from datetime import datetime

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    correlation_id = get_correlation_id()

    # Log error
    logger.error(f"Request failed: {exc.message}", extra={
        "correlationId": correlation_id,
        "errorCode": exc.error_code,
        "statusCode": exc.status_code,
        "details": exc.details
    })

    # Send error response (no stack trace to client)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "statusCode": exc.status_code,
                "correlationId": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "details": exc.details
            }
        }
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    correlation_id = get_correlation_id()

    # Log unexpected error with stack trace
    logger.exception("Unexpected error occurred", extra={
        "correlationId": correlation_id,
        "error": str(exc)
    })

    # Send generic error response
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "statusCode": 500,
                "correlationId": correlation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

---

## Caching Strategy

### Read-Through Cache (Future Enhancement)

**Current State**: No caching (direct MongoDB queries)

**Planned**: Redis caching for frequently accessed products

```python
import redis.asyncio as redis
import json

# Cache configuration
CACHE_TTL = 5 * 60  # 5 minutes

# Redis client
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Cache key pattern
def get_cache_key(product_id: str) -> str:
    return f"product:{product_id}"

# Read-through cache
async def get_product_by_id(id: str) -> dict:
    # 1. Check cache
    cache_key = get_cache_key(id)
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. Query database
    product = await collection.find_one({"_id": ObjectId(id)})
    if not product:
        return None

    # 3. Store in cache
    await redis_client.setex(cache_key, CACHE_TTL, json.dumps(product, default=str))
    return product

# Cache invalidation on update
async def update_product(id: str, data: dict) -> dict:
    product = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": data},
        return_document=True
    )

    # Invalidate cache
    await redis_client.delete(get_cache_key(id))
    return product
```

---

## Testing Strategy

### Test Pyramid

```
      ┌─────────┐
      │   E2E   │  10% (Full user workflows)
      └─────────┘
    ┌─────────────┐
    │ Integration │  30% (API endpoints + DB)
    └─────────────┘
  ┌─────────────────┐
  │      Unit       │  60% (Services, utils, pure logic)
  └─────────────────┘
```

### Unit Tests (Pytest)

**Example: Product Service**:

```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.product_service import ProductService
from app.utils.errors import DuplicateSkuError

@pytest.fixture
def mock_repo():
    return Mock(
        create=AsyncMock(),
        find_by_sku=AsyncMock()
    )

@pytest.fixture
def mock_publisher():
    return Mock(publish_product_created=AsyncMock())

@pytest.fixture
def product_service(mock_repo, mock_publisher):
    return ProductService(mock_repo, mock_publisher)


class TestProductService:
    @pytest.mark.asyncio
    async def test_create_product_success(self, product_service, mock_repo, mock_publisher):
        # Arrange
        product_data = {"name": "Test Product", "sku": "TEST-001", "price": 29.99}
        created_product = {**product_data, "_id": "123"}

        mock_repo.find_by_sku.return_value = None  # No duplicate
        mock_repo.create.return_value = created_product

        # Act
        result = await product_service.create_product(product_data)

        # Assert
        assert result == created_product
        mock_publisher.publish_product_created.assert_called_once_with(created_product)

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, product_service, mock_repo):
        # Arrange
        mock_repo.find_by_sku.return_value = {"sku": "TEST-001"}

        # Act & Assert
        with pytest.raises(DuplicateSkuError):
            await product_service.create_product({"sku": "TEST-001", "name": "Test", "price": 10})
```

### Integration Tests (httpx + mongomock)

**Example: Product API**:

```python
import pytest
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient
from app.main import app
from app.core.database import get_database

@pytest.fixture
async def mock_db():
    client = AsyncMongoMockClient()
    db = client["test_db"]
    return db

@pytest.fixture
async def test_client(mock_db):
    app.dependency_overrides[get_database] = lambda: mock_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token():
    return generate_test_token({"role": "admin"})


class TestProductAPI:
    @pytest.mark.asyncio
    async def test_create_product_success(self, test_client, admin_token):
        # Arrange
        product_data = {
            "name": "Test Product",
            "sku": "TEST-001",
            "price": 29.99,
            "status": "active"
        }

        # Act
        response = await test_client.post(
            "/api/products",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["name"] == "Test Product"
        assert response.json()["sku"] == "TEST-001"

    @pytest.mark.asyncio
    async def test_create_product_unauthorized(self, test_client):
        # Act
        response = await test_client.post(
            "/api/products",
            json={"name": "Test", "sku": "TEST", "price": 10}
        )

        # Assert
        assert response.status_code == 401
```

### Test Coverage Goals

- **Overall**: 80% code coverage
- **Services**: 90% (critical business logic)
- **Routers**: 80% (API endpoints)
- **Repositories**: 70% (data access)
- **Utils**: 85% (pure functions)

---

## Performance Optimization

### Database Optimization

1. **Indexes**: Created on frequently queried fields (SKU, status, category, parentId)
2. **Projection**: Only select needed fields in queries
3. **Pagination**: Limit result set size (default: 20 items)
4. **Aggregation Pipeline**: Use MongoDB aggregation for complex queries

### Query Optimization Examples

```python
# ❌ Bad: Select all fields
cursor = collection.find({"status": "active"})
products = await cursor.to_list(length=None)

# ✅ Good: Project only needed fields
cursor = collection.find(
    {"status": "active"},
    {"name": 1, "sku": 1, "price": 1, "images.url": 1}
)
products = await cursor.to_list(length=20)

# ✅ Good: Use indexes with hint
cursor = collection.find({
    "status": "active",
    "taxonomy.category": "Clothing"
}).hint([("status", 1), ("taxonomy.category", 1)])
products = await cursor.to_list(length=20)
```

### Response Optimization

1. **Compression**: Enable gzip compression via FastAPI middleware
2. **Field Selection**: Only return necessary fields in API responses
3. **Denormalized Data**: Store computed values (review aggregates, availability) to avoid joins

### Monitoring & Profiling

```python
# Track query performance
import time
from app.core.logger import logger
from prometheus_client import Histogram

query_duration_histogram = Histogram(
    'product_query_duration_seconds',
    'Query duration in seconds',
    ['operation']
)

async def track_query_performance(operation: str, query_func):
    start_time = time.time()
    result = await query_func()
    duration = time.time() - start_time

    # Log slow queries
    if duration > 0.2:  # 200ms
        logger.warning(f"Slow query detected: {operation}", extra={
            "operation": operation,
            "duration": duration
        })

    # Record metric
    query_duration_histogram.labels(operation=operation).observe(duration)
    return result

# Usage
product = await track_query_performance(
    "get_product_by_id",
    lambda: collection.find_one({"_id": ObjectId(id)})
)
```

---

## Security Considerations

### JWT Validation

```python
# Dependency for JWT validation
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_PUBLIC_KEY"),
            algorithms=["RS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### Input Sanitization

```python
# Prevent NoSQL injection in MongoDB queries
def sanitize_query(query: dict) -> dict:
    """Remove $ and . operators from user input"""
    sanitized = {}
    for key, value in query.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_query(value)
        elif isinstance(value, str):
            # Remove MongoDB operators
            sanitized[key] = value.replace("$", "").replace(".", "")
        else:
            sanitized[key] = value
    return sanitized

# Use Pydantic for validation (automatic XSS prevention)
from pydantic import BaseModel, validator

class CreateProductRequest(BaseModel):
    name: str
    sku: str
    price: float

    @validator('name', 'sku')
    def sanitize_string(cls, v):
        # Pydantic automatically validates and sanitizes
        return v.strip()
```

### Rate Limiting (at BFF/Gateway Level)

Rate limiting is handled upstream at BFF/API Gateway, not in Product Service.

---

## Deployment Configuration

### Environment Variables

```bash
# Server
PORT=8003
ENVIRONMENT=production

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/products
MONGODB_POOL_MIN=10
MONGODB_POOL_MAX=50

# Dapr
DAPR_HOST=localhost
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001

# Message Broker
PUBSUB_COMPONENT_NAME=pubsub
PRODUCT_EVENTS_TOPIC=product.events

# JWT
JWT_PUBLIC_KEY=<base64-encoded-public-key>

# Logging
LOG_LEVEL=info

# Feature Flags
ENABLE_BADGE_AUTOMATION=true
ENABLE_BULK_IMPORT=true
```

### Dockerfile

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application
COPY app ./app

FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/app ./app

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8003

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Health Checks

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# Liveness probe
@app.get("/health")
async def health():
    return {"status": "ok"}

# Readiness probe
@app.get("/health/ready")
async def health_ready(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        # Ping database
        await db.command("ping")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": "disconnected"}
        )
```

---

## Future Enhancements

1. **GraphQL API**: Alternative to REST for flexible queries
2. **Elasticsearch Integration**: Full-text search offloading
3. **Redis Caching**: Cache frequently accessed products
4. **CQRS Full Implementation**: Separate read/write models
5. **Event Sourcing**: Store complete event history
6. **Batch Processing**: Background jobs for badge automation using Celery
7. **Multi-Region Support**: Geographic data replication

---

## References

- [Product Service PRD](./PRD.md)
- [Platform Architecture](../../../docs/PLATFORM_ARCHITECTURE.md)
- [Dapr Documentation](https://docs.dapr.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## Document Change History

| Version | Date       | Changes                           | Author  |
| ------- | ---------- | --------------------------------- | ------- |
| 1.0     | 2025-11-03 | Initial architecture document     | AI Team |
| 2.0     | 2025-11-03 | Converted to Python/FastAPI stack | AI Team |
