# Dapr Configuration

This directory contains Dapr component and configuration files for the Product Service.

## Overview

Product Service uses Dapr for:
- **Event Publishing**: Publish product lifecycle events via Dapr Pub/Sub
- **State Management**: Cache product data using Dapr State Store
- **Distributed Tracing**: Automatic tracing with OpenTelemetry

## Directory Structure

```
dapr/
├── components/           # Dapr component definitions
│   ├── pubsub-rabbitmq.yaml    # RabbitMQ pub/sub component
│   └── statestore-redis.yaml   # Redis state store component
├── config/              # Dapr configuration
│   └── config.yaml      # Tracing and metrics configuration
└── README.md           # This file
```

## Components

### 1. Pub/Sub (RabbitMQ)

**File**: `components/pubsub-rabbitmq.yaml`

**Purpose**: Framework-agnostic message publishing for product events

**Configuration**:
- **Component Name**: `aioutlet-pubsub`
- **Type**: `pubsub.rabbitmq`
- **Exchange**: `aioutlet.events` (topic exchange)
- **Features**:
  - Durable messages (survives broker restart)
  - Persistent delivery mode
  - Automatic retry on failure
  - Prefetch count: 10

**Events Published**:
- `product.created` - New product created (PRD REQ-3.1.1)
- `product.updated` - Product details changed (PRD REQ-3.1.2)
- `product.deleted` - Product soft-deleted (PRD REQ-3.1.3)
- `product.price.changed` - Product price updated (PRD REQ-3.1.4)
- `product.back.in.stock` - Product back in stock (PRD REQ-3.1.5)

**Environment Variables**:
```bash
RABBITMQ_HOST=rabbitmq:5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=admin123
```

### 2. State Store (Redis)

**File**: `components/statestore-redis.yaml`

**Purpose**: Caching and distributed locking

**Configuration**:
- **Component Name**: `statestore`
- **Type**: `state.redis`
- **Features**:
  - TTL support for cache expiration
  - Actor state store enabled
  - Distributed locking for bulk import jobs

**Use Cases**:
- Product detail caching (5 minutes TTL)
- Category lists caching (1 hour TTL)
- Bestseller lists caching (1 hour TTL)
- Distributed locks for bulk import workers

**Environment Variables**:
```bash
REDIS_HOST=redis:6379
REDIS_PASSWORD=
```

### 3. Configuration (Tracing & Metrics)

**File**: `config/config.yaml`

**Purpose**: Dapr runtime configuration

**Features**:
- **Distributed Tracing**:
  - Sampling rate: 100% (all requests traced)
  - Backend: Zipkin
  - Endpoint: `http://zipkin:9411/api/v2/spans`
- **Metrics**:
  - Prometheus-compatible metrics enabled
  - Endpoint: `http://localhost:9090/metrics` (Dapr sidecar)

## Running with Dapr

### Local Development

#### 1. Install Dapr CLI

```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | /bin/bash

# Windows (PowerShell)
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"
```

#### 2. Initialize Dapr

```bash
dapr init
```

This installs:
- Dapr runtime
- Redis (for state store)
- Zipkin (for tracing)
- Placement service (for actors)

#### 3. Run Product Service with Dapr

```bash
# Terminal 1: Start MongoDB and RabbitMQ
docker-compose up mongodb rabbitmq redis

# Terminal 2: Run Product Service with Dapr sidecar
dapr run \
  --app-id product-service \
  --app-port 8081 \
  --dapr-http-port 3500 \
  --dapr-grpc-port 50001 \
  --components-path ./dapr/components \
  --config ./dapr/config/config.yaml \
  -- python -m uvicorn src.main:app --host 0.0.0.0 --port 8081
```

**Ports**:
- `8081` - Product Service API
- `3500` - Dapr HTTP API
- `50001` - Dapr gRPC API
- `9090` - Dapr metrics (Prometheus)

### Docker Compose

Add to `docker-compose.yml`:

```yaml
product-service:
  build: .
  ports:
    - "8081:8081"
  environment:
    - PORT=8081
    - DAPR_HTTP_PORT=3500
    - SERVICE_NAME=product-service
  depends_on:
    - mongodb
    - rabbitmq
    - redis

product-service-dapr:
  image: "daprio/daprd:latest"
  command:
    [
      "./daprd",
      "-app-id", "product-service",
      "-app-port", "8081",
      "-dapr-http-port", "3500",
      "-dapr-grpc-port", "50001",
      "-components-path", "/components",
      "-config", "/config/config.yaml"
    ]
  volumes:
    - "./dapr/components:/components"
    - "./dapr/config:/config"
  depends_on:
    - product-service
  network_mode: "service:product-service"
```

### Kubernetes Deployment

#### 1. Install Dapr on Kubernetes

```bash
dapr init -k
```

#### 2. Deploy Components

```bash
kubectl apply -f dapr/components/pubsub-rabbitmq.yaml
kubectl apply -f dapr/components/statestore-redis.yaml
kubectl apply -f dapr/config/config.yaml
```

#### 3. Annotate Deployment

Add Dapr annotations to your deployment YAML:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-service
spec:
  template:
    metadata:
      labels:
        app: product-service
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "product-service"
        dapr.io/app-port: "8081"
        dapr.io/config: "daprConfig"
    spec:
      containers:
      - name: product-service
        image: product-service:latest
        ports:
        - containerPort: 8081
```

## Testing Event Publishing

### 1. Using Dapr CLI

```bash
# Publish test event
dapr publish --publish-app-id product-service --pubsub aioutlet-pubsub --topic product.created --data '{"productId": "123", "name": "Test Product"}'
```

### 2. Using Python Client

```python
from dapr.clients import DaprClient

with DaprClient() as client:
    client.publish_event(
        pubsub_name='aioutlet-pubsub',
        topic_name='product.created',
        data='{"productId": "123", "name": "Test Product"}'
    )
```

### 3. Using HTTP API

```bash
curl -X POST http://localhost:3500/v1.0/publish/aioutlet-pubsub/product.created \
  -H "Content-Type: application/json" \
  -d '{"productId": "123", "name": "Test Product"}'
```

## Monitoring

### View Dapr Dashboard

```bash
dapr dashboard
```

Access at: http://localhost:8080

### View Traces (Zipkin)

Access at: http://localhost:9411

### View Metrics (Prometheus)

```bash
curl http://localhost:9090/metrics
```

## Troubleshooting

### Dapr Sidecar Not Starting

```bash
# Check Dapr logs
dapr logs --app-id product-service

# Check component status
dapr components -k
```

### Events Not Publishing

1. **Check Dapr sidecar is running**:
   ```bash
   curl http://localhost:3500/v1.0/healthz
   ```

2. **Verify component configuration**:
   ```bash
   kubectl get components
   ```

3. **Check RabbitMQ connection**:
   ```bash
   # View RabbitMQ management UI
   http://localhost:15672
   # Default: guest/guest
   ```

### State Store Not Working

1. **Check Redis connection**:
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

2. **Test state store**:
   ```bash
   # Save state
   curl -X POST http://localhost:3500/v1.0/state/statestore \
     -H "Content-Type: application/json" \
     -d '[{"key": "test", "value": "hello"}]'

   # Get state
   curl http://localhost:3500/v1.0/state/statestore/test
   ```

## Security Considerations

### Production Checklist

- [ ] Use TLS for RabbitMQ connections
- [ ] Configure Redis authentication
- [ ] Rotate RabbitMQ credentials
- [ ] Use Kubernetes secrets for sensitive data
- [ ] Enable mTLS between Dapr sidecars
- [ ] Configure network policies
- [ ] Set up monitoring and alerting
- [ ] Review Dapr security best practices: https://docs.dapr.io/operations/security/

### Environment-Specific Configuration

Create separate component files for each environment:

```
dapr/
├── components/
│   ├── dev/
│   │   ├── pubsub-rabbitmq.yaml
│   │   └── statestore-redis.yaml
│   ├── staging/
│   │   ├── pubsub-rabbitmq.yaml
│   │   └── statestore-redis.yaml
│   └── prod/
│       ├── pubsub-rabbitmq.yaml
│       └── statestore-redis.yaml
```

## References

- **Dapr Documentation**: https://docs.dapr.io
- **Dapr Python SDK**: https://github.com/dapr/python-sdk
- **Dapr Pub/Sub**: https://docs.dapr.io/developing-applications/building-blocks/pubsub/
- **Dapr State Store**: https://docs.dapr.io/developing-applications/building-blocks/state-management/
- **RabbitMQ Component**: https://docs.dapr.io/reference/components-reference/supported-pubsub/setup-rabbitmq/
- **Redis Component**: https://docs.dapr.io/reference/components-reference/supported-state-stores/setup-redis/

## Support

For issues or questions:
- Product Service Issues: https://github.com/aioutlet/product-service/issues
- Dapr Issues: https://github.com/dapr/dapr/issues
- Dapr Community: https://discord.com/invite/ptHhX6jc34
