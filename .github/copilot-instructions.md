# GitHub Copilot Instructions: Product Service

## Business Context

📋 **Read First**: All business requirements are in [`docs/PRD.md`](../docs/PRD.md). This file covers **HOW** to implement those requirements using our chosen technology stack.

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

#### Data Storage (Implementing PRD REQ-4.x)

- **Database**: MongoDB
- **Driver**: motor (async MongoDB driver)
- **Why**:
  - Flexible schema for product catalog
  - Excellent text search capabilities
  - Good performance for read-heavy workloads
  - Easy hierarchical data storage (department/category/subcategory)

#### Event Publishing (Implementing PRD REQ-3.x)

- **Solution**: Dapr Pub/Sub
- **Component Name**: `aioutlet-pubsub`
- **Backend**: RabbitMQ (configurable via Dapr component)
- **Why Dapr**:
  - Framework-agnostic (can switch to Kafka/Azure Service Bus without code changes)
  - Built-in retries and resilience (meets PRD NFR-2.3)
  - Automatic distributed tracing (meets PRD NFR-5.1)
  - Fire-and-forget pattern (meets PRD REQ-3.5)
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
    Implements PRD REQ-3.x: Event Publishing requirements.
    """

    def __init__(self):
        self.dapr_http_port = os.getenv('DAPR_HTTP_PORT', '3500')
        self.dapr_grpc_port = os.getenv('DAPR_GRPC_PORT', '50001')
        self.pubsub_name = 'aioutlet-pubsub'
        self.service_name = os.getenv('SERVICE_NAME', 'product-service')

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Publish an event via Dapr pub/sub.

        Meets Requirements:
        - PRD REQ-3.1 to REQ-3.4: Specific event publishing
        - PRD REQ-3.5: Fire-and-forget, don't fail on publish error
        - PRD NFR-2.3: Automatic retries via Dapr
        - PRD NFR-5.1: Correlation ID propagation

        Args:
            event_type: Event type (e.g., 'product.created')
            data: Event payload
            correlation_id: Correlation ID for tracing
        """
        try:
            # Build event payload matching PRD event schema
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
            # Per PRD REQ-3.5: Log but don't fail the operation
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

#### Event Consumption (Implementing PRD REQ-12.x)

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
    Updates product rating aggregates (REQ-12.1).
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
    Updates product availability status (REQ-12.2).
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
    Evaluates Best Seller badge criteria (REQ-12.3).
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

### Background Workers (Implementing PRD REQ-12.4)

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

### Caching Strategy (Implementing PRD NFR-1.x)

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

- Review aggregates (5 second target per REQ-12.1)
- Inventory availability (10 second target per REQ-12.2)
- Sales rank and badges (1 hour refresh per REQ-12.3)
- Q&A counts (30 second target per REQ-14.1)

**Trade-offs**:

- **Benefit**: Massive performance improvement (no cross-service transactions)
- **Cost**: UI may show slightly stale data (e.g., review count off by 1)
- **Mitigation**: Clear UI indicators ("Updated 2 minutes ago")

### Observability (Implementing PRD NFR-5.x)

#### Distributed Tracing (PRD NFR-5.1)

- **Solution**: Dapr automatic tracing with OpenTelemetry
- **Implementation**:
  - Correlation IDs passed through all operations
  - Dapr automatically injects trace context into all pub/sub messages
  - OpenTelemetry compatible (works with Zipkin, Jaeger, Application Insights)

#### Logging (PRD NFR-5.2)

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

#### Metrics (PRD NFR-5.3)

- **Format**: Prometheus-compatible endpoints
- **Metrics to Track**:
  - Request count per endpoint
  - Request latency percentiles (p50, p95, p99)
  - Error count by type
  - Database query duration
  - Event publishing attempts/failures

#### Health Checks (PRD NFR-5.4)

- **Endpoint**: `/health` (liveness)
- **Endpoint**: `/health/ready` (readiness)
- **Checks**: MongoDB connectivity

### Security (Implementing PRD NFR-4.x)

#### Authentication (PRD NFR-4.1)

- **Method**: JWT token validation
- **Middleware**: FastAPI dependency injection
- **Token Source**: Authorization header (`Bearer <token>`)

#### Authorization (PRD NFR-4.2)

- **Admin Operations**: Require `admin` role in JWT
- **Function**: `verify_admin_access(user)` in `src/security`
- **Error**: 403 Forbidden for non-admin users

#### Input Validation (PRD NFR-4.3)

- **Library**: Pydantic models (FastAPI built-in)
- **ObjectId Validation**: `validate_object_id()` utility
- **Sanitization**: Automatic via Pydantic

## Dapr Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=product-service
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

### When Implementing Event Publishing (PRD REQ-3.x)

**Prompt Template**:

```
"Implement PRD REQ-3.1 (publish product.created event) using Dapr pub/sub.
Event schema must match PRD docs/PRD.md section 'Event Schemas'.
Use DaprPublisher from src/services/dapr_publisher.py."
```

**DO ✅**:

- Use Dapr pub/sub via `DaprClient`
- Match event schema exactly as in PRD
- Include correlation ID for tracing
- Use try-except to prevent failures from breaking API
- Log all publishing attempts

**DON'T ❌**:

- Use direct RabbitMQ/Kafka client (bypasses Dapr abstraction)
- Block API response waiting for event confirmation
- Raise exceptions on publishing failures
- Skip correlation ID
- Call message broker service directly

### When Implementing CRUD Operations (PRD REQ-1.x)

**Prompt Template**:

```
"Implement PRD REQ-1.2 (update product) in product_controller.py.
Follow existing pattern with history tracking. Publish product.updated
event using Dapr publisher."
```

**DO ✅**:

- Validate admin permissions first
- Track changes in history array
- Update `updated_at` timestamp
- Publish appropriate events after successful DB operation
- Return full product object

**DON'T ❌**:

- Skip validation
- Forget to update timestamps
- Publish events before DB commit
- Return partial objects

### When Implementing Search/Filter (PRD REQ-2.x)

**Prompt Template**:

```
"Implement PRD REQ-2.2 (hierarchical filtering) in product_controller.py.
Support department/category/subcategory filters with pagination (offset-based
and cursor-based per REQ-2.5)."
```

**DO ✅**:

- Use MongoDB aggregation pipelines for efficiency
- Return only active products for customer-facing endpoints
- Include pagination metadata (total, page, limit, has_next, has_previous)
- Index fields used in filtering
- Implement both offset-based (simple) and cursor-based (large datasets) pagination
- Limit offset-based pagination to first 10,000 results (500 pages × 20 items)
- Use cursor encoding for stateless pagination (base64 encode sort key + ID)

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

### When Adding Logging (PRD NFR-5.2)

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

- ✅ All PRD REQ-\* implemented
- ✅ All PRD NFR-\* validated
- ✅ API contracts match PRD exactly
- ✅ Event schemas match PRD exactly
- ✅ Admin operations validate permissions
- ✅ Events reach consumers (audit, notification services)
- ✅ Soft-deleted products not in search results
- ✅ SKU uniqueness enforced

## Common Copilot Prompts for This Service

### Creating New Feature

```
"Read docs/PRD.md REQ-X.X. Implement this requirement in
src/controllers/product_controller.py using the patterns in
.github/copilot-instructions.md. Include proper logging and
event publishing."
```

### Migrating Existing Code to Dapr

```
"Refactor src/controllers/product_controller.py to use Dapr for event
publishing. Replace any existing event publishing code with DaprPublisher
from src/services/dapr_publisher.py. Maintain same event schemas from
PRD docs/PRD.md."
```

### Adding Tests

```
"Create tests/integration/test_events.py that verifies PRD REQ-3.1
(product.created event) is published via Dapr. Mock Dapr client as
shown in .github/copilot-instructions.md testing section."
```

### Reviewing Code

```
"@workspace Review src/controllers/product_controller.py.
Verify it implements PRD requirements REQ-1.x and REQ-3.x correctly.
Check if Dapr pub/sub is used properly per .github/copilot-instructions.md.
List any deviations or issues."
```

## Performance Optimization

### Database Indexes (PRD NFR-1.3)

Required indexes for performance:

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

### Key Metrics to Monitor

1. **Latency**: p95 < 200ms for reads, < 500ms for writes
2. **Throughput**: Handle 1,000 req/s sustained
3. **Error Rate**: < 0.1%
4. **Event Publishing Success**: > 99.9%
5. **Database Connection Pool**: Utilization < 80%

### Alert Thresholds

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

| PRD Requirement         | Implementation Approach                                              |
| ----------------------- | -------------------------------------------------------------------- |
| REQ-1.x (CRUD)          | FastAPI endpoints + MongoDB + Motor driver                           |
| REQ-2.x (Search)        | MongoDB text indexes + aggregation pipelines                         |
| REQ-3.x (Events Pub)    | Dapr Pub/Sub publisher                                               |
| REQ-4.x (Validation)    | Pydantic models + custom validators                                  |
| REQ-5.x (Admin)         | JWT role checking + history tracking                                 |
| REQ-6.x (Inter-service) | FastAPI endpoint (optimized query)                                   |
| REQ-7.x (Bulk Import)   | Background worker + Dapr State Store for job tracking                |
| REQ-8.x (Variations)    | MongoDB parent-child relationships + reference fields                |
| REQ-9.x (Attributes)    | MongoDB flexible schema + category-based validation                  |
| REQ-10.x (Badges)       | Badge collection + TTL indexes for expiration                        |
| REQ-11.x (SEO)          | URL slug fields + unique indexes + metadata objects                  |
| REQ-12.1 (Review Sync)  | Dapr subscription + denormalized review aggregates                   |
| REQ-12.2 (Inventory)    | Dapr subscription + availability status field                        |
| REQ-12.3 (Badges Auto)  | Dapr subscription + badge evaluation service                         |
| REQ-12.4 (Bulk Worker)  | Background worker consuming self-published events + distributed lock |
| REQ-13.x (Videos)       | Video URL array + metadata objects                                   |
| REQ-14.x (Q&A)          | Dapr subscription + denormalized Q&A counts                          |
| REQ-15.x (Size Charts)  | Category-level size chart references                                 |
| REQ-16.x (Restrictions) | Restriction flags + metadata fields                                  |
| NFR-1.x (Performance)   | Async I/O + DB indexes + pagination + Redis caching via Dapr         |
| NFR-2.x (Reliability)   | Error handling + Dapr retries + idempotent event handlers            |
| NFR-3.x (Scalability)   | Stateless design + horizontal scaling + eventual consistency         |
| NFR-4.x (Security)      | JWT validation + role-based access control                           |
| NFR-5.x (Observability) | Structured logging + Dapr tracing + Prometheus metrics               |

---

**Remember**: This file describes **HOW** to implement Product Service. The **WHAT** (business requirements) is in [`docs/PRD.md`](../docs/PRD.md). Keep them synchronized but separate!
