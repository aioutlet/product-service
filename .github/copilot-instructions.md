# GitHub Copilot Instructions: Product Service

## Business Context

📋 **Read First**: All business requirements are in [`docs/PRD.md`](../docs/PRD.md). This file covers **HOW** to implement those requirements using our chosen technology stack.

**PRD Structure Reference**:

- **Section 2**: Technical Architecture (Technology Stack, Data Model, Events, Environment Variables)
- **Section 3**: API Specifications (32+ endpoints with full request/response examples, Error Code Catalog)
- **Section 4**: Functional Requirements (Product Management, Search, Validation, Admin, Variations)
- **Section 5**: Non-Functional Requirements (Performance, Security, Scalability, Observability)

**Key PRD Sections**:

- **Section 2.3**: Event-Driven Integration (Outbound/Inbound events with JSON schemas)
- **Section 2.7**: Environment Variables (80+ variables for configuration)
- **Section 3.2-3.5**: API Endpoints with complete request/response examples
- **Section 3.6**: Error Code Catalog (50+ standardized error codes)
- **Section 4.1-4.6**: Functional requirements for features
- **Section 5.1-5.7**: Non-functional requirements (performance, security, etc.)

## Service Overview

- **Service Name**: Product Service
- **Pattern**: Publisher & Consumer (publishes product events, consumes review/inventory/analytics events)
- **Language**: Python 3.12
- **Framework**: FastAPI
- **Database**: MongoDB
- **Event Publishing**: Dapr Pub/Sub (framework-agnostic messaging)
- **Event Consumption**: Dapr Pub/Sub subscriptions (eventual consistency pattern)

## Technology Stack & Implementation Decisions

### Core Technologies

#### Programming Language & Framework

- **Language**: Python 3.12
- **Framework**: FastAPI
- **Why**:
  - High performance async capabilities
  - Automatic OpenAPI documentation
  - Modern Python type hints
  - Easy to test and maintain

#### Data Storage (Implementing PRD Section 4.1-4.6)

- **Database**: MongoDB
- **Driver**: motor (async MongoDB driver)
- **Why**:
  - Flexible schema for product catalog
  - Excellent text search capabilities
  - Good performance for read-heavy workloads
  - Easy hierarchical data storage (department/category/subcategory)

#### Event Publishing (Implementing PRD Section 2.3.2)

- **Solution**: Dapr Pub/Sub
- **Component Name**: `aioutlet-pubsub`
- **Backend**: RabbitMQ (configurable via Dapr component)
- **Why Dapr**:
  - Framework-agnostic (can switch to Kafka/Azure Service Bus without code changes)
  - Built-in retries and resilience (meets PRD Section 5.3)
  - Automatic distributed tracing (meets PRD Section 5.6)
  - Fire-and-forget pattern (meets PRD Section 2.3.2)
  - At-least-once delivery guarantee (meets PRD event delivery requirements)
  - No custom message broker service needed

**Implementation Pattern with Dapr**:

```python
# src/services/dapr_publisher.py
from dapr.clients import DaprClient
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.observability import logger

class DaprPublisher:
    """
    Publisher for sending events via Dapr pub/sub.
    Implements PRD Section 2.3.2: Outbound Events requirements.
    """

    def __init__(self):
        self.dapr_http_port = os.getenv('DAPR_HTTP_PORT', '3500')
        self.dapr_grpc_port = os.getenv('DAPR_GRPC_PORT', '50001')
        self.pubsub_name = 'aioutlet-pubsub'
        self.service_name = os.getenv('NAME', 'product-service')

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Publish an event via Dapr pub/sub.

        Meets Requirements:
        - PRD Section 2.3.2: Specific event publishing (8 event types)
        - PRD Section 5.3.2: Fire-and-forget, don't fail on publish error
        - PRD Section 5.6.1: Correlation ID propagation for distributed tracing

        Args:
            event_type: Event type (e.g., 'product.created')
            data: Event payload
            correlation_id: Correlation ID for tracing
        """
        try:
            # Build event payload matching PRD event schema (Section 2.3.2)
            event_payload = {
                'eventType': event_type,
                'eventId': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': self.service_name,
                'correlationId': correlation_id,
                'data': data
            }

            # Publish via Dapr (using HTTP endpoint)
            # Dapr handles retries, durability, and routing
            with DaprClient(f'http://localhost:{self.dapr_http_port}') as client:
                client.publish_event(
                    pubsub_name=self.pubsub_name,
                    topic_name=event_type,  # Topic = event type
                    data=json.dumps(event_payload),
                    data_content_type='application/json'
                )

            logger.info(
                f"Published event via Dapr: {event_type}",
                metadata={
                    'correlationId': correlation_id,
                    'eventType': event_type,
                    'source': self.service_name,
                    'transport': 'dapr'
                }
            )

        except Exception as e:
            # Per PRD Section 5.3.2: Log but don't fail the operation
            logger.error(
                f"Failed to publish event via Dapr: {str(e)}",
                metadata={
                    'correlationId': correlation_id,
                    'eventType': event_type,
                    'error': str(e),
                    'errorType': type(e).__name__
                }
            )
            # Don't raise - publishing failures shouldn't break main flow

# Singleton instance
_dapr_publisher = None

def get_dapr_publisher() -> DaprPublisher:
    """Get singleton Dapr publisher instance"""
    global _dapr_publisher
    if _dapr_publisher is None:
        _dapr_publisher = DaprPublisher()
    return _dapr_publisher
```

#### Event Consumption (Implementing PRD Section 2.3.3)

- **Solution**: Dapr Pub/Sub subscriptions
- **Pattern**: HTTP endpoints that Dapr calls when events arrive
- **Subscription Config**: Declarative YAML files in `dapr/subscriptions/`
- **Consistency Model**: Eventual consistency (denormalized data may be slightly stale)
- **Idempotency**: All event handlers MUST be idempotent (handle duplicate events)

**Implementation Pattern with Dapr Subscriptions**:

```python
# src/api/event_subscriptions.py
from fastapi import FastAPI, Request
from typing import Dict, Any
from src.services.review_aggregator import update_review_aggregates
from src.services.inventory_sync import update_availability_status
from src.services.badge_manager import evaluate_badge_criteria
from src.observability import logger

app = FastAPI()

@app.post('/dapr/subscribe')
async def subscribe():
    """
    Dapr calls this endpoint to discover which events this service subscribes to.
    Returns array of subscription configurations.
    """
    subscriptions = [
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'review.created',
            'route': '/events/review-created'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'review.updated',
            'route': '/events/review-updated'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'review.deleted',
            'route': '/events/review-deleted'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'inventory.stock.updated',
            'route': '/events/inventory-updated'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'analytics.product.sales.updated',
            'route': '/events/sales-updated'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'analytics.product.views.updated',
            'route': '/events/views-updated'
        },
        {
            'pubsubname': 'aioutlet-pubsub',
            'topic': 'product.question.created',
            'route': '/events/question-created'
        }
    ]
    return subscriptions


@app.post('/events/review-created')
async def handle_review_created(request: Request):
    """
    Handles review.created events from Review Service.
    Updates product rating aggregates (PRD Section 2.3.3 - review.created).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        rating = event['data']['rating']
        verified = event['data'].get('verifiedPurchase', False)

        # Update review aggregates (idempotent operation)
        await update_review_aggregates(product_id, rating, verified, operation='add')

        logger.info(
            f"Processed review.created event",
            metadata={
                'productId': product_id,
                'rating': rating,
                'correlationId': event.get('correlationId')
            }
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(f"Failed to process review.created event: {str(e)}")
        # Return SUCCESS to prevent Dapr retries (log error for manual review)
        # Alternatively, return error to trigger retry if transient failure
        return {'status': 'RETRY'}  # Dapr will retry this event


@app.post('/events/inventory-updated')
async def handle_inventory_updated(request: Request):
    """
    Handles inventory.stock.updated events from Inventory Service.
    Updates product availability status (PRD Section 2.3.3 - inventory.stock.updated).
    """
    try:
        event = await request.json()
        sku = event['data']['sku']
        product_id = event['data'].get('productId')
        available_qty = event['data']['availableQuantity']
        low_stock_threshold = event['data'].get('lowStockThreshold', 10)

        # Update availability status (idempotent)
        was_out_of_stock = await update_availability_status(
            sku,
            product_id,
            available_qty,
            low_stock_threshold
        )

        # If product came back in stock, publish notification event
        if was_out_of_stock and available_qty > 0:
            from src.services.dapr_publisher import get_dapr_publisher
            publisher = get_dapr_publisher()
            await publisher.publish(
                'product.back.in.stock',
                {
                    'productId': product_id,
                    'sku': sku,
                    'availableQuantity': available_qty
                },
                event.get('correlationId')
            )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(f"Failed to process inventory event: {str(e)}")
        return {'status': 'RETRY'}


@app.post('/events/sales-updated')
async def handle_sales_updated(request: Request):
    """
    Handles analytics.product.sales.updated events.
    Evaluates Best Seller badge criteria (PRD Section 2.3.3 - analytics events).
    """
    try:
        event = await request.json()
        product_id = event['data']['productId']
        category = event['data']['category']
        sales_last_30_days = event['data']['salesLast30Days']
        category_rank = event['data']['categoryRank']

        # Evaluate badge criteria and auto-assign/remove
        await evaluate_badge_criteria(
            product_id,
            badge_type='best-seller',
            metrics={
                'salesLast30Days': sales_last_30_days,
                'categoryRank': category_rank
            },
            criteria_threshold=100  # Top 100 = Best Seller
        )

        return {'status': 'SUCCESS'}

    except Exception as e:
        logger.error(f"Failed to process sales event: {str(e)}")
        return {'status': 'RETRY'}
```

**Key Event Consumption Patterns**:

1. **Idempotency**: All handlers MUST handle duplicate events safely

   - Use upsert operations where possible
   - Check current state before applying changes
   - Use event IDs to deduplicate if needed

2. **Error Handling**:

   - Return `{'status': 'SUCCESS'}` for successfully processed events
   - Return `{'status': 'RETRY'}` for transient failures (Dapr will retry)
   - Return `{'status': 'DROP'}` for invalid events (no retry)

3. **Performance**:

   - Keep handlers fast (< 100ms target)
   - Use async database operations
   - Don't block on external calls

4. **Consistency**:
   - Accept eventual consistency (data may be seconds behind source)
   - Don't use consumed data for critical business logic
   - Denormalized data is for read optimization only

### Background Workers (Implementing PRD Section 4.4.2)

#### Bulk Import Worker Pattern

- **Solution**: Separate worker process consuming bulk import jobs
- **Concurrency**: Use Dapr Actors or Python asyncio for job processing
- **Job Queue**: Self-published events (`product.bulk.import.job.created`)
- **Distribution**: Distributed locking via Dapr State Store

**Implementation Pattern**:

```python
# src/workers/bulk_import_worker.py
import asyncio
from dapr.clients import DaprClient
from src.services.bulk_import_processor import process_import_batch

async def bulk_import_worker():
    """
    Background worker that processes bulk import jobs.
    Consumes product.bulk.import.job.created events.
    """
    @app.post('/events/bulk-import-job-created')
    async def handle_bulk_import_job(request: Request):
        event = await request.json()
        job_id = event['data']['jobId']
        file_path = event['data']['filePath']
        total_rows = event['data']['totalRows']
        mode = event['data']['mode']  # partial-import or all-or-nothing

        # Acquire distributed lock (prevent duplicate processing)
        lock_key = f"bulk-import-lock-{job_id}"
        with DaprClient() as client:
            lock_acquired = client.try_lock('statestore', lock_key, owner=job_id)

            if not lock_acquired:
                return {'status': 'DROP'}  # Another worker processing this job

            try:
                # Process in batches
                batch_size = 100
                for batch_offset in range(0, total_rows, batch_size):
                    # Check for cancellation
                    job_status = await get_job_status(job_id)
                    if job_status == 'cancelled':
                        break

                    # Process batch
                    success_count, failure_count = await process_import_batch(
                        file_path,
                        batch_offset,
                        batch_size,
                        mode
                    )

                    # Publish progress event
                    await publish_progress_event(job_id, batch_offset + batch_size, total_rows)

                # Publish completion event
                await publish_completion_event(job_id)

            finally:
                # Release lock
                client.unlock('statestore', lock_key, owner=job_id)

        return {'status': 'SUCCESS'}
```

### Caching Strategy (Implementing PRD Section 5.1)

#### Caching with Dapr State Store

- **Solution**: Redis via Dapr State Store
- **Cache Layer**: Between API and MongoDB
- **Invalidation**: On product update events (self-subscription)

**What to Cache**:

- **Product Details** (high read volume):

  - Key: `product:{productId}`
  - TTL: 5 minutes
  - Invalidate on: product.updated, product.deleted events

- **Category Lists** (relatively static):

  - Key: `category:{categoryId}:products`
  - TTL: 1 hour
  - Invalidate on: product category changes

- **Bestseller Lists** (computed data):
  - Key: `bestsellers:{categoryId}`
  - TTL: 1 hour
  - Refresh on: analytics events

**Implementation Pattern**:

```python
# src/services/product_cache.py
from dapr.clients import DaprClient
import json

class ProductCache:
    def __init__(self):
        self.store_name = 'statestore'
        self.ttl_seconds = 300  # 5 minutes

    async def get_product(self, product_id: str):
        """Get product from cache"""
        with DaprClient() as client:
            state = client.get_state(self.store_name, f"product:{product_id}")
            if state.data:
                return json.loads(state.data)
        return None

    async def set_product(self, product_id: str, product_data: dict):
        """Cache product with TTL"""
        with DaprClient() as client:
            client.save_state(
                self.store_name,
                f"product:{product_id}",
                json.dumps(product_data),
                state_metadata={'ttlInSeconds': str(self.ttl_seconds)}
            )

    async def invalidate_product(self, product_id: str):
        """Remove product from cache"""
        with DaprClient() as client:
            client.delete_state(self.store_name, f"product:{product_id}")
```

**Cache-Aside Pattern in Controller**:

```python
# src/controllers/product_controller.py
from src.services.product_cache import ProductCache

cache = ProductCache()

@app.get('/api/products/{product_id}')
async def get_product(product_id: str):
    # Try cache first
    product = await cache.get_product(product_id)

    if product:
        return product  # Cache hit

    # Cache miss - load from database
    product = await product_repository.find_by_id(product_id)

    if product:
        # Store in cache for next request
        await cache.set_product(product_id, product)

    return product


@app.put('/api/products/{product_id}')
async def update_product(product_id: str, updates: dict):
    # Update database
    product = await product_repository.update(product_id, updates)

    # Invalidate cache
    await cache.invalidate_product(product_id)

    # Publish event
    await publisher.publish('product.updated', product)

    return product
```

### Data Consistency Patterns

**Strong Consistency** (transactional within MongoDB):

- Product CRUD operations
- SKU uniqueness constraints
- Price updates
- Product variation relationships

**Eventual Consistency** (accept delay):

- Review aggregates (5 second target per Section 2.3.3)
- Inventory availability (10 second target per Section 2.3.3)
- Sales rank and badges (1 hour refresh per Section 2.3.3)
- Q&A counts (30 second target per Section 2.3.3)

**Trade-offs**:

- **Benefit**: Massive performance improvement (no cross-service transactions)
- **Cost**: UI may show slightly stale data (e.g., review count off by 1)
- **Mitigation**: Clear UI indicators ("Updated 2 minutes ago")

### Observability (Implementing PRD Section 5.6)

#### Distributed Tracing (PRD Section 5.6.1)

- **Solution**: Dapr automatic tracing with OpenTelemetry
- **Implementation**:
  - Correlation IDs passed through all operations
  - Dapr automatically injects trace context into all pub/sub messages
  - OpenTelemetry compatible (works with Zipkin, Jaeger, Application Insights)

#### Logging (PRD Section 5.6.2)

- **Library**: Python `logging` with structured JSON output
- **Format**: JSON with timestamp, level, message, metadata
- **Levels**: Configurable via environment variable
- **Required Fields**:
  - timestamp
  - level
  - event (business event name)
  - correlationId (if available)
  - userId (if available)
  - error details (if applicable)

#### Metrics (PRD Section 5.6.3)

- **Format**: Prometheus-compatible endpoints
- **Metrics to Track**:
  - Request count per endpoint
  - Request latency percentiles (p50, p95, p99)
  - Error count by type
  - Database query duration
  - Event publishing attempts/failures

#### Health Checks (PRD Section 3.5)

- **Endpoint**: `/health` (liveness) - Section 3.5.1
- **Endpoint**: `/health/ready` (readiness) - Section 3.5.2
- **Checks**: MongoDB connectivity

### Security (Implementing PRD Section 5.4)

#### Authentication (PRD Section 5.4.1)

- **Method**: JWT token validation
- **Middleware**: FastAPI dependency injection
- **Token Source**: Authorization header (`Bearer <token>`)

#### Authorization (PRD Section 5.4.4)

- **Admin Operations**: Require `admin` role in JWT
- **Function**: `verify_admin_access(user)` in `src/security`
- **Error**: 403 Forbidden for non-admin users

#### Input Validation (PRD Section 5.4.3)

- **Library**: Pydantic models (FastAPI built-in)
- **ObjectId Validation**: `validate_object_id()` utility
- **Sanitization**: Automatic via Pydantic

### Environment Configuration (PRD Section 2.7)

All environment variables are comprehensively documented in **PRD Section 2.7** with 80+ variables across 11 categories:

- **Section 2.7.1**: Database Configuration (MongoDB connection, pooling)
- **Section 2.7.2**: Message Broker Configuration (RabbitMQ settings)
- **Section 2.7.3**: Dapr Configuration (sidecar ports, pub/sub component name)
- **Section 2.7.4**: Authentication & Authorization (JWT public key, algorithm)
- **Section 2.7.5**: Service Configuration (service name, port, log level, CORS)
- **Section 2.7.6**: Performance & Caching (rate limiting, caching, pagination limits)
- **Section 2.7.7**: File Upload Configuration (import/image size limits)
- **Section 2.7.8**: Monitoring & Observability (metrics, tracing, Jaeger)
- **Section 2.7.9**: Health Check Configuration (probe timeouts)
- **Section 2.7.10**: Event Publishing Configuration (retry settings, batching)
- **Section 2.7.11**: Example Configuration Files (development, production, Kubernetes)

**Key Environment Variables for Dapr Integration**:

```bash
# Dapr Configuration (Section 2.7.3)
DAPR_HTTP_PORT=3500          # Dapr HTTP sidecar port
DAPR_GRPC_PORT=50001         # Dapr gRPC sidecar port
DAPR_PUBSUB_NAME=product-pubsub  # Pub/sub component name
DAPR_APP_ID=product-service  # Dapr application identifier
DAPR_APP_PORT=8003           # Port where product service listens

# Database (Section 2.7.1)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=aioutlet_products

# Message Broker (Section 2.7.2)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=secretpassword

# Authentication (Section 2.7.4)
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\n...
JWT_ALGORITHM=RS256

# Service (Section 2.7.5)
NAME=product-service
ENVIRONMENT=production
LOG_LEVEL=info
```

**Refer to PRD Section 2.7.11 for complete .env.development, .env.production, and Kubernetes ConfigMap examples.**

### Error Handling (PRD Section 3.6)

All API error codes are standardized and documented in **PRD Section 3.6: Error Code Catalog** with 50+ error codes.

**Error Code Categories**:

- **Section 3.6.1**: Client Error Codes (4xx) - 21 codes including validation, authentication, authorization, not found, conflict
- **Section 3.6.2**: Server Error Codes (5xx) - 9 codes for internal errors, database failures, timeouts
- **Section 3.6.3**: Business Logic Error Codes - 10 domain-specific error codes
- **Section 3.6.4**: Error Response Format - Standard structure with examples

**Standard Error Response Format** (Section 3.6.4):

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error description",
  "details": {
    "field": "specific_field_name",
    "value": "invalid_value",
    "constraint": "validation_constraint"
  },
  "correlationId": "req-abc-123",
  "timestamp": "2025-11-04T19:30:00Z",
  "path": "/api/products",
  "method": "POST"
}
```

**Implementation Pattern**:

```python
# src/errors/error_handler.py
from fastapi import HTTPException
from typing import Dict, Any, Optional

class APIError(HTTPException):
    """
    Standard API error following PRD Section 3.6.4 format.
    All error codes from Section 3.6.1-3.6.3.
    """
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.error_code = error_code
        self.correlation_id = correlation_id
        self.details = details

        super().__init__(
            status_code=status_code,
            detail={
                "error": error_code,
                "message": message,
                "details": details,
                "correlationId": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# Common error factories (using codes from PRD Section 3.6)
class ProductErrors:
    @staticmethod
    def not_found(product_id: str, correlation_id: str = None):
        return APIError(
            error_code="PRODUCT_NOT_FOUND",
            message=f"Product with ID '{product_id}' does not exist",
            status_code=404,
            details={"productId": product_id},
            correlation_id=correlation_id
        )

    @staticmethod
    def duplicate_sku(sku: str, correlation_id: str = None):
        return APIError(
            error_code="DUPLICATE_SKU",
            message=f"SKU '{sku}' already exists",
            status_code=409,
            details={"sku": sku},
            correlation_id=correlation_id
        )

    @staticmethod
    def validation_error(field: str, value: Any, constraint: str, correlation_id: str = None):
        return APIError(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=400,
            details={
                "field": field,
                "value": value,
                "constraint": constraint
            },
            correlation_id=correlation_id
        )

    @staticmethod
    def admin_required(correlation_id: str = None):
        return APIError(
            error_code="ADMIN_ROLE_REQUIRED",
            message="Admin role required for this operation",
            status_code=403,
            correlation_id=correlation_id
        )

# Usage in controllers
@app.post('/api/products')
async def create_product(product: ProductCreate, correlation_id: str = None):
    # Check for duplicate SKU
    existing = await product_repo.find_by_sku(product.sku)
    if existing:
        raise ProductErrors.duplicate_sku(product.sku, correlation_id)

    # Validate admin permission
    if not user.has_role('admin'):
        raise ProductErrors.admin_required(correlation_id)

    # Create product...
```

**Key Error Codes to Use** (from Section 3.6.1-3.6.3):

- `VALIDATION_ERROR` (400) - Request validation failed
- `UNAUTHORIZED` (401) - Authentication failed
- `ADMIN_ROLE_REQUIRED` (403) - Admin role required
- `PRODUCT_NOT_FOUND` (404) - Product doesn't exist
- `DUPLICATE_SKU` (409) - SKU already exists
- `PAYLOAD_TOO_LARGE` (413) - File exceeds size limit
- `TOO_MANY_REQUESTS` (429) - Rate limit exceeded
- `INTERNAL_SERVER_ERROR` (500) - Unexpected server error
- `DATABASE_ERROR` (500) - Database operation failed
- `SERVICE_UNAVAILABLE` (503) - Service temporarily unavailable

**Refer to PRD Section 3.6 for the complete catalog of 50+ error codes with descriptions and client actions.**

### API Request/Response Examples (PRD Section 3.2-3.5)

All API endpoints have comprehensive request/response examples in the PRD:

- **Section 3.2**: Product Management APIs (18 endpoints with full JSON examples)

  - 3.2.1-3.2.4: Core CRUD operations
  - 3.2.5-3.2.6: Product existence check and batch lookup
  - 3.2.7-3.2.9: Bulk operations (import, job status, variations)
  - 3.2.10-3.2.13: Badge management and SEO metadata
  - 3.2.14-3.2.18: Template download, error reports, image upload, variations

- **Section 3.3**: Product Discovery APIs (5 endpoints)

  - 3.3.1-3.3.2: Search with offset and cursor pagination
  - 3.3.3: Category-based product listing
  - 3.3.4: Autocomplete suggestions
  - 3.3.5: Trending products

- **Section 3.4**: Admin APIs (authorization requirements, audit trail)

- **Section 3.5**: Health Check APIs
  - 3.5.1: Liveness probe
  - 3.5.2: Readiness probe with dependency health

**When implementing endpoints, refer to PRD Section 3 for exact request/response formats, authentication headers, and error responses.**

## Dapr Configuration

### Environment Variables

```bash
# Service Configuration
NAME=product-service
PORT=8081

# Dapr Configuration
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001

# Database Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=product_db

# Observability
LOG_LEVEL=info
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

### Dapr Sidecar Configuration

- **App ID**: `product-service`
- **App Port**: `8081`
- **Dapr HTTP Port**: `3500`
- **Dapr gRPC Port**: `50001`
- **Components Path**: `./dapr/components/`

### Dapr Component Files to Create

#### 1. `dapr/components/pubsub-rabbitmq.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: aioutlet-pubsub
spec:
  type: pubsub.rabbitmq
  version: v1
  metadata:
    - name: host
      value: 'amqp://admin:admin123@rabbitmq:5672'
    - name: exchangeName
      value: 'aioutlet.events'
    - name: exchangeKind
      value: 'topic'
    - name: durable
      value: 'true'
    - name: deletedWhenUnused
      value: 'false'
    - name: autoAck
      value: 'false'
    - name: deliveryMode
      value: '2' # persistent
    - name: requeueInFailure
      value: 'true'
    - name: prefetchCount
      value: '10'
scopes:
  - product-service
```

#### 2. `dapr/config/config.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: daprConfig
spec:
  tracing:
    samplingRate: '1'
    zipkin:
      endpointAddress: 'http://zipkin:9411/api/v2/spans'
  metric:
    enabled: true
```

#### 3. `dapr/components/statestore-redis.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: 'redis:6379'
    - name: redisPassword
      value: ''
    - name: actorStateStore
      value: 'true'
scopes:
  - product-service
```

### Docker Compose Integration

Add Dapr sidecar to `docker-compose.yml`:

```yaml
product-service:
  build: .
  ports:
    - '8081:8081'
  environment:
    - PORT=8081
    - DAPR_HTTP_PORT=3500
  depends_on:
    - mongodb
    - rabbitmq

product-service-dapr:
  image: 'daprio/daprd:latest'
  command:
    [
      './daprd',
      '-app-id',
      'product-service',
      '-app-port',
      '8081',
      '-dapr-http-port',
      '3500',
      '-dapr-grpc-port',
      '50001',
      '-components-path',
      '/components',
      '-config',
      '/config/config.yaml',
    ]
  volumes:
    - './dapr/components:/components'
    - './dapr/config:/config'
  depends_on:
    - product-service
  network_mode: 'service:product-service'
```

## Implementation Guide: Dapr Event Publishing

### Files to Create

1. **`src/services/dapr_publisher.py`** - Dapr pub/sub implementation (see pattern above)
2. **`dapr/components/pubsub-rabbitmq.yaml`** - Dapr pub/sub component configuration
3. **`dapr/config/config.yaml`** - Dapr configuration with tracing enabled

### Files to Modify

1. **`src/controllers/product_controller.py`** - Import and use `dapr_publisher`
2. **`requirements.txt`** - Add Dapr SDK: `dapr>=1.12.0`
3. **`docker-compose.yml`** - Add Dapr sidecar container

### Implementation Steps

1. **Add Dapr SDK**: Update `requirements.txt` with `dapr>=1.12.0` and `dapr-ext-grpc>=1.12.0`
2. **Create Dapr Publisher**: Implement `src/services/dapr_publisher.py` following the pattern above
3. **Create Dapr Components**: Add component YAML files in `dapr/components/`
4. **Update Controllers**: Replace any existing event publishing with Dapr publisher:

   ```python
   from src.services.dapr_publisher import get_dapr_publisher

   publisher = get_dapr_publisher()
   await publisher.publish('product.created', product_data, correlation_id)
   ```

5. **Add Dapr Sidecar**: Update docker-compose with sidecar container (see Docker Compose Integration section)
6. **Test Event Flow**: Verify events reach consuming services (audit-service, notification-service)
7. **Monitor Logs**: Check for successful event publishing in structured logs

## Code Generation Guidelines for Copilot

### When Implementing Event Publishing (PRD Section 2.3.2)

**Prompt Template**:

```
"Implement product.created event publishing (PRD Section 2.3.2) using Dapr pub/sub.
Event schema must match PRD docs/PRD.md Section 2.3.2.
Use DaprPublisher from src/services/dapr_publisher.py.
Use error code from Section 3.6 if needed."
```

**DO ✅**:

- Use Dapr pub/sub via `DaprClient`
- Match event schema exactly as in PRD Section 2.3.2
- Include correlation ID for tracing
- Use try-except to prevent failures from breaking API
- Log all publishing attempts

**DON'T ❌**:

- Use direct RabbitMQ/Kafka client (bypasses Dapr abstraction)
- Block API response waiting for event confirmation
- Raise exceptions on publishing failures
- Skip correlation ID
- Call message broker service directly

### When Implementing CRUD Operations (PRD Section 4.1)

**Prompt Template**:

```
"Implement product update endpoint (PRD Section 4.1.2 and API example Section 3.2.3).
Follow history tracking pattern. Publish product.updated event per Section 2.3.2.
Use error codes from Section 3.6.1-3.6.3."
```

**DO ✅**:

- Validate admin permissions first (Section 5.4.4)
- Track changes in history array
- Update `updated_at` timestamp
- Publish appropriate events after successful DB operation (Section 2.3.2)
- Return full product object matching Section 3.2.3 response
- Use standardized error codes from Section 3.6

**DON'T ❌**:

- Skip validation
- Forget to update timestamps
- Publish events before DB commit
- Return partial objects
- Use custom error formats (use Section 3.6.4 format)

### When Implementing Search/Filter (PRD Section 4.2)

**Prompt Template**:

```
"Implement hierarchical category filtering (PRD Section 4.2.2 and API Section 3.3.1).
Support department/category/subcategory filters with pagination.
Use both offset-based (Section 3.3.1) and cursor-based (Section 3.3.2) pagination."
```

**DO ✅**:

- Use MongoDB aggregation pipelines for efficiency
- Return only active products for customer-facing endpoints
- Include pagination metadata matching Section 3.3.1 response format
- Index fields used in filtering (Section 2.5)
- Implement both offset-based (simple) and cursor-based (large datasets) pagination
- Limit offset-based pagination to first 10,000 results (500 pages × 20 items)
- Use cursor encoding for stateless pagination (base64 encode sort key + ID)
- Return error code `DEEP_PAGINATION_NOT_SUPPORTED` for page > 500 (Section 3.6.3)

**DON'T ❌**:

- Load all products into memory
- Skip pagination
- Return inactive products to customers
- Create N+1 query patterns
- Allow deep offset pagination (> 10,000 results)
- Calculate total count for cursor-based pagination (performance hit)

**Pagination Implementation Pattern**:

```python
# src/controllers/product_controller.py

# OFFSET-BASED PAGINATION (for first 10,000 results)
@app.get('/api/products/search')
async def search_products(
    q: str = None,
    page: int = 1,
    limit: int = 20,
    sort: str = 'relevance'
):
    # Validate deep pagination
    max_page = 500
    if page > max_page:
        raise HTTPException(
            status_code=400,
            detail=f"Page must be <= {max_page}. Use /api/products/search/cursor for deep pagination."
        )

    # Validate limit
    if limit > 100:
        limit = 100

    # Calculate offset
    skip = (page - 1) * limit

    # Build query
    query = build_search_query(q, filters)

    # Get total count (cache for 30 seconds)
    cache_key = f"search_count:{hash(query)}"
    total = await cache.get(cache_key)
    if not total:
        total = await products_collection.count_documents(query)
        await cache.set(cache_key, total, ttl=30)

    # Get results with pagination
    cursor = products_collection.find(query).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)

    return {
        "products": products,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": math.ceil(total / limit),
            "has_next": skip + limit < total,
            "has_previous": page > 1
        }
    }


# CURSOR-BASED PAGINATION (for large datasets, no total count)
@app.get('/api/products/search/cursor')
async def search_products_cursor(
    q: str = None,
    cursor: str = None,
    limit: int = 20,
    sort: str = 'price-asc'
):
    # Validate limit
    if limit > 100:
        limit = 100

    # Build base query
    query = build_search_query(q, filters)

    # Decode cursor to get last item's position
    if cursor:
        cursor_data = decode_cursor(cursor)  # base64 decode
        # Add cursor condition to query (e.g., price > last_price OR (price == last_price AND _id > last_id))
        query = add_cursor_condition(query, cursor_data, sort)

    # Get results (limit + 1 to check if more exist)
    cursor_obj = products_collection.find(query).sort(sort).limit(limit + 1)
    products = await cursor_obj.to_list(length=limit + 1)

    # Check if more results exist
    has_more = len(products) > limit
    if has_more:
        products = products[:limit]  # Remove extra item

    # Generate next cursor from last item
    next_cursor = None
    if has_more and products:
        last_item = products[-1]
        next_cursor = encode_cursor(last_item, sort)  # base64 encode

    # Generate previous cursor (optional, more complex)
    previous_cursor = None
    if cursor:
        # Would need to reverse query and get previous items
        # Often omitted in cursor pagination
        pass

    return {
        "products": products,
        "pagination": {
            "next_cursor": next_cursor,
            "previous_cursor": previous_cursor,
            "has_more": has_more,
            "limit": limit
        }
    }


# CURSOR ENCODING/DECODING HELPERS
import base64
import json

def encode_cursor(item: dict, sort_field: str) -> str:
    """Encode cursor from last item"""
    cursor_data = {
        "id": str(item["_id"]),
        "sort_value": item.get(sort_field)
    }
    json_str = json.dumps(cursor_data)
    return base64.b64encode(json_str.encode()).decode()

def decode_cursor(cursor: str) -> dict:
    """Decode cursor to get position"""
    json_str = base64.b64decode(cursor.encode()).decode()
    return json.loads(json_str)

def add_cursor_condition(query: dict, cursor_data: dict, sort: str) -> dict:
    """Add cursor condition to MongoDB query"""
    sort_field = parse_sort_field(sort)  # e.g., "price-asc" -> "price"
    sort_direction = parse_sort_direction(sort)  # e.g., "price-asc" -> 1

    if sort_direction == 1:  # Ascending
        query["$or"] = [
            {sort_field: {"$gt": cursor_data["sort_value"]}},
            {
                sort_field: cursor_data["sort_value"],
                "_id": {"$gt": ObjectId(cursor_data["id"])}
            }
        ]
    else:  # Descending
        query["$or"] = [
            {sort_field: {"$lt": cursor_data["sort_value"]}},
            {
                sort_field: cursor_data["sort_value"],
                "_id": {"$lt": ObjectId(cursor_data["id"])}
            }
        ]

    return query
```

**Performance Tips**:

1. **Index Sort Fields**: Create compound index on (sort_field, \_id)

   ```python
   await collection.create_index([("price", 1), ("_id", 1)])
   await collection.create_index([("created_at", -1), ("_id", -1)])
   ```

2. **Cache Total Counts**: Cache for 30 seconds to reduce DB load

   ```python
   cache_key = f"search_count:{query_hash}"
   total = await cache.get_or_compute(cache_key, compute_func, ttl=30)
   ```

3. **Limit Deep Pagination**: Reject page > 500 for offset-based

   ```python
   if page > 500:
       return {"error": "Use cursor-based pagination for deep results"}
   ```

4. **Skip Total Count for Cursors**: Don't calculate total in cursor mode
   - Saves expensive COUNT() operation
   - Users don't need total for infinite scroll

### When Adding Logging (PRD Section 5.6.2)

**DO ✅**:

```python
logger.info(
    "Product created successfully",
    metadata={
        "event": "product_created",
        "productId": product_id,
        "correlationId": correlation_id,
        "userId": user.user_id if user else None
    }
)
```

**DON'T ❌**:

```python
print(f"Product created: {product_id}")  # No
logger.info("Created product")  # Too vague
```

### When Handling Errors (PRD Section 3.6)

**DO ✅**:

```python
# Use standardized error codes from Section 3.6
from src.errors.error_handler import ProductErrors

# Validation error
if not product.price or product.price < 0:
    raise ProductErrors.validation_error(
        field="price",
        value=product.price,
        constraint="must be positive",
        correlation_id=correlation_id
    )

# Not found error
product = await product_repo.find_by_id(product_id)
if not product:
    raise ProductErrors.not_found(product_id, correlation_id)

# Admin permission error
if not user.has_role('admin'):
    raise ProductErrors.admin_required(correlation_id)
```

**DON'T ❌**:

```python
# Don't use generic HTTP exceptions
raise HTTPException(status_code=404, detail="Not found")  # No

# Don't use custom error formats
return {"error": "Product not found"}  # No - doesn't match Section 3.6.4 format
```

## Testing Guidelines

### Unit Tests

- Mock Dapr client: `unittest.mock.patch('dapr.clients.DaprClient')`
- Test business logic in isolation
- Verify event payloads match PRD schemas

### Integration Tests

- Use TestContainers for MongoDB
- Verify actual event publishing to RabbitMQ
- Test end-to-end flows (API → DB → Event)

### Test Checklist (Per PRD Acceptance Criteria)

- ✅ All functional requirements (Section 4.x) implemented
- ✅ All non-functional requirements (Section 5.x) validated
- ✅ API contracts match PRD Section 3 exactly
- ✅ Event schemas match PRD Section 2.3.2 and 2.3.3 exactly
- ✅ Error codes match PRD Section 3.6 catalog
- ✅ Admin operations validate permissions (Section 5.4.4)
- ✅ Events reach consumers (audit, notification services)
- ✅ Soft-deleted products not in search results
- ✅ SKU uniqueness enforced

## Common Copilot Prompts for This Service

### Creating New Feature

```
"Read docs/PRD.md Section 4.x.x. Implement this requirement in
src/controllers/product_controller.py using the patterns in
.github/copilot-instructions.md. Follow API format from Section 3.x.x.
Use error codes from Section 3.6. Include proper logging per Section 5.6.2
and event publishing per Section 2.3.2."
```

### Migrating Existing Code to Dapr

```
"Refactor src/controllers/product_controller.py to use Dapr for event
publishing. Replace any existing event publishing code with DaprPublisher
from src/services/dapr_publisher.py. Maintain same event schemas from
PRD Section 2.3.2."
```

### Adding Tests

```
"Create tests/integration/test_events.py that verifies product.created
event (PRD Section 2.3.2) is published via Dapr. Mock Dapr client as
shown in .github/copilot-instructions.md testing section."
```

### Reviewing Code

```
"@workspace Review src/controllers/product_controller.py.
Verify it implements PRD Section 4.1 (CRUD operations) and Section 2.3.2
(event publishing) correctly. Check if Dapr pub/sub is used properly per
.github/copilot-instructions.md. Verify error handling uses Section 3.6
error codes. List any deviations or issues."
```

### Implementing New API Endpoint

```
"Implement GET /api/products/trending endpoint following PRD Section 3.3.5.
Use exact request/response format from PRD. Support query parameters for
category and timeWindow. Use error codes from Section 3.6 for validation errors.
Add structured logging per Section 5.6.2."
```

## Performance Optimization

### Database Indexes (PRD Section 2.5)

Required indexes for performance (documented in PRD Section 2.5):

```python
# In database setup/migration
await collection.create_index([("name", "text"), ("description", "text"), ("tags", "text")])
await collection.create_index("sku", unique=True)
await collection.create_index("is_active")
await collection.create_index("department")
await collection.create_index("category")
await collection.create_index("price")
```

### Query Optimization

- Use projection to limit returned fields
- Use pagination for all list operations
- Avoid loading full product history unless needed

## Monitoring & Alerts

### Key Metrics to Monitor (PRD Section 5.6.3)

1. **Latency**: p95 < 200ms for reads, < 500ms for writes (Section 5.1.1)
2. **Throughput**: Handle 1,000 req/s sustained (Section 5.1.2)
3. **Error Rate**: < 0.1% (Section 5.2)
4. **Event Publishing Success**: > 99.9% (Section 5.3.2)
5. **Database Connection Pool**: Utilization < 80% (Section 5.1.3)

### Alert Thresholds (PRD Section 5.6.3 - Alerting Thresholds)

- Error rate > 1% for 5 minutes
- p95 latency > 500ms for 5 minutes
- Event publishing failures > 10 in 1 minute
- Database connection failures > 3 in 1 minute

## Dependencies

### Python Packages (requirements.txt)

```txt
# Core Framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# Database
motor==3.3.2  # Async MongoDB
pymongo==4.6.0

# Dapr (Pub/Sub, State Store, Actors)
dapr>=1.12.0
dapr-ext-grpc>=1.12.0

# Background Jobs
celery==5.3.4  # Alternative to Dapr Actors for worker pattern
redis==5.0.1  # For caching and job queue

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Observability
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0

# Data Processing (for bulk import)
openpyxl==3.1.2  # Excel file parsing
pandas==2.1.3  # Data manipulation (optional, for large imports)
```

## Reference Documentation

### Internal References

- **Business Requirements**: [`docs/PRD.md`](../docs/PRD.md) (framework-agnostic)
- **API Documentation**: Auto-generated at `/docs` (FastAPI Swagger UI)
- **Architecture Decisions**: `../docs/ARCHITECTURE.md` (to be created)

### External References

- **Dapr Python SDK**: https://docs.dapr.io/developing-applications/sdks/python/
- **Dapr Pub/Sub**: https://docs.dapr.io/developing-applications/building-blocks/pubsub/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Motor (MongoDB)**: https://motor.readthedocs.io/

---

## Quick Reference: PRD Requirements → Implementation

| PRD Section       | Requirement                   | Implementation Approach                                            |
| ----------------- | ----------------------------- | ------------------------------------------------------------------ |
| **Section 4.1**   | Product CRUD Operations       | FastAPI endpoints + MongoDB + Motor driver                         |
| **Section 4.1.1** | Create Products               | POST /api/products (Section 3.2.1) + validation + event publishing |
| **Section 4.1.2** | Update Products               | PUT /api/products/{id} (Section 3.2.3) + history tracking          |
| **Section 4.1.3** | Soft Delete Products          | DELETE /api/products/{id} (Section 3.2.4) + status flag            |
| **Section 4.1.4** | Prevent Duplicate SKUs        | MongoDB unique index on SKU field                                  |
| **Section 4.2**   | Product Discovery & Search    | MongoDB text indexes + aggregation pipelines                       |
| **Section 4.2.1** | Text Search                   | MongoDB full-text search with weighted fields                      |
| **Section 4.2.2** | Hierarchical Filtering        | Query filters on taxonomy fields (department/category/subcategory) |
| **Section 4.2.3** | Price Range Filtering         | MongoDB range queries with indexes                                 |
| **Section 4.2.5** | Pagination                    | Offset-based (Section 3.3.1) and cursor-based (Section 3.3.2)      |
| **Section 4.2.6** | Trending Products             | GET /api/products/trending (Section 3.3.5) with analytics data     |
| **Section 4.3**   | Data Consistency & Validation | Pydantic models + custom validators                                |
| **Section 4.4**   | Administrative Features       | Role-based access control + audit logging                          |
| **Section 4.4.2** | Bulk Product Operations       | Background worker + Dapr State Store for job tracking              |
| **Section 4.4.3** | Badge Management              | Badge collection + TTL indexes for expiration + auto-evaluation    |
| **Section 4.5**   | Product Variations            | MongoDB parent-child relationships + reference fields              |
| **Section 4.6**   | Enhanced Product Attributes   | MongoDB flexible schema + category-based validation                |
| **Section 2.3.2** | Event Publishing (Outbound)   | Dapr Pub/Sub publisher (8 event types)                             |
| **Section 2.3.3** | Event Consumption (Inbound)   | Dapr subscriptions + denormalized data (11 event types)            |
| **Section 2.4**   | Data Model                    | MongoDB collections with flexible schema                           |
| **Section 2.5**   | Database Indexes              | Compound indexes for performance (text, unique, taxonomy)          |
| **Section 2.6**   | Inter-Service Communication   | Synchronous REST APIs for product lookups                          |
| **Section 2.7**   | Environment Variables         | 80+ variables across 11 categories for configuration               |
| **Section 3.2**   | Product Management APIs       | 18 endpoints with full request/response examples                   |
| **Section 3.3**   | Product Discovery APIs        | 5 endpoints with pagination and filtering                          |
| **Section 3.4**   | Admin APIs                    | Role-based authorization + audit trail                             |
| **Section 3.5**   | Health Check APIs             | Liveness (3.5.1) and readiness (3.5.2) probes                      |
| **Section 3.6**   | Error Code Catalog            | 50+ standardized error codes (4xx, 5xx, business logic)            |
| **Section 5.1**   | Performance Requirements      | Async I/O + DB indexes + pagination + Redis caching via Dapr       |
| **Section 5.2**   | Scalability Requirements      | Stateless design + horizontal scaling                              |
| **Section 5.3**   | Availability Requirements     | Error handling + Dapr retries + idempotent event handlers          |
| **Section 5.4**   | Security Requirements         | JWT validation + role-based access control + input validation      |
| **Section 5.5**   | Reliability Requirements      | Health checks + circuit breakers + retry logic                     |
| **Section 5.6**   | Observability Requirements    | Structured logging + Dapr tracing + Prometheus metrics             |
| **Section 5.7**   | Error Handling Requirements   | Standard error format (3.6.4) + correlation IDs                    |

---

**Remember**: This file describes **HOW** to implement Product Service. The **WHAT** (business requirements) is in [`docs/PRD.md`](../docs/PRD.md). Keep them synchronized but separate!
