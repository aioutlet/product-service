# Product Service

The `product-service` is responsible for product catalog management, inventory tracking, and product lifecycle operations for the AIOutlet platform. It is a core microservice in the product management architecture.

**Architecture Pattern**: Pure Publisher (Dapr Pub/Sub)

- Publishes events via Dapr SDK to RabbitMQ backend
- No direct RabbitMQ or consumer dependencies
- Consumes events via webhooks (future implementation)

---

## Features

- Product CRUD operations (Create, Read, Update, Delete)
- Product search and filtering
- Category management
- Inventory tracking
- Product pricing management
- Event publishing for product lifecycle changes (created, updated, deleted)
- Structured logging and error handling
- Distributed tracing support

---

## Architecture

This service is built with **Python FastAPI**, using **Motor** (async MongoDB driver) for database operations and **Dapr SDK** for service mesh capabilities.

The microservice follows a **Dapr-only architecture**:
- No fallback to direct HTTP or environment variables
- All secrets managed via Dapr Secret Store
- Service invocation through Dapr sidecar
- Distributed tracing via Dapr configuration

---

## Project Structure

```
app/
├── api/              # API route handlers
├── clients/          # Dapr clients (secrets, service invocation)
├── core/             # Core configuration, logging, errors
├── db/               # Database connection and configuration
├── middleware/       # Custom middleware (trace context)
├── models/           # Pydantic models and MongoDB schemas
├── services/         # Business logic layer
└── validators/       # Input validation logic
main.py              # FastAPI application entry point
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- MongoDB instance (local or Docker)
- **Dapr v1.16.2+** (required - no fallback mode)
- Docker (for infrastructure: MongoDB, RabbitMQ, Redis, OTEL Collector, Jaeger)

### Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start infrastructure** (MongoDB, RabbitMQ, Redis, OTEL Collector, Jaeger):
   ```bash
   cd ../../scripts/docker-compose
   docker-compose -f docker-compose.infrastructure.yml up -d
   docker-compose -f docker-compose.services.yml up product-mongodb -d
   ```

3. **Configure secrets** - Create `.dapr/secrets.json`:
   ```json
   {
     "MONGODB_CONNECTION_STRING": "mongodb://localhost:27017/product_service_db",
     "JWT_SECRET": "your-super-secret-jwt-key-change-in-production"
   }
   ```

4. **Run the service with Dapr**:
   ```bash
   # Using run script (recommended)
   ./run.sh      # Linux/Mac
   .\run.ps1     # Windows
   ```

5. **Access the service**:
   - Service API: `http://localhost:1001/api`
   - API Documentation: `http://localhost:1001/docs`
   - Dapr sidecar: `http://localhost:3501`
   - Health check: `http://localhost:3501/v1.0/invoke/product-service/method/health`
   - Jaeger tracing UI: `http://localhost:16686`

### Environment Variables

Configuration is handled by `app/core/config.py` with sensible defaults for local development.

Secrets are managed via **Dapr Secret Store** (`.dapr/components/secrets.yaml`).

---

## API Endpoints

### Products
- `GET /api/products` — List all products (with pagination)
- `POST /api/products` — Create a new product
- `GET /api/products/{id}` — Get product by ID
- `PUT /api/products/{id}` — Update product
- `DELETE /api/products/{id}` — Delete product

### Admin
- `GET /api/admin/products/stats` — Product statistics

### Operational
- `GET /health` — Health check
- `GET /health/ready` — Readiness check
- `GET /health/live` — Liveness check

---

## Development

### Debug Mode
Use VS Code "Debug" launch configuration to run with breakpoints.

### Testing
```bash
pytest
pytest --cov=app tests/
```

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

---

## License

MIT License

---

## Contact

For questions or support, reach out to the AIOutlet dev team.
