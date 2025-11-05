#!/bin/bash
# Dapr run script for Product Service

echo "🚀 Starting Product Service with Dapr..."

# Set Dapr app configuration
export DAPR_APP_ID=product-service
export DAPR_HTTP_PORT=3500
export DAPR_GRPC_PORT=50001
export DAPR_APP_PORT=8003

echo "📦 Dapr Configuration:"
echo "   App ID: $DAPR_APP_ID"
echo "   HTTP Port: $DAPR_HTTP_PORT"
echo "   gRPC Port: $DAPR_GRPC_PORT"
echo "   App Port: $DAPR_APP_PORT"
echo ""

# Check if Dapr is installed
if ! command -v dapr &> /dev/null; then
    echo "❌ Dapr CLI is not installed!"
    echo "Please install Dapr CLI: https://docs.dapr.io/getting-started/install-dapr-cli/"
    exit 1
fi

# Check if Redis is running (for pub/sub)
echo "🔍 Checking Redis availability..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "Please start Redis: redis-server"
    echo "Or use Docker: docker run -d --name redis -p 6379:6379 redis:alpine"
    exit 1
fi
echo "✅ Redis is running"

# Check if MongoDB is running
echo "🔍 Checking MongoDB availability..."
if ! mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "❌ MongoDB is not running!"
    echo "Please start MongoDB or check your connection settings"
    exit 1
fi
echo "✅ MongoDB is running"

echo ""
echo "🏁 Starting Product Service with Dapr sidecar..."
echo ""

# Start the product service with Dapr
dapr run \
  --app-id $DAPR_APP_ID \
  --app-port $DAPR_APP_PORT \
  --dapr-http-port $DAPR_HTTP_PORT \
  --dapr-grpc-port $DAPR_GRPC_PORT \
  --components-path .dapr/components \
  --config .dapr/config.yaml \
  -- python -m uvicorn src.main:app --host 0.0.0.0 --port $DAPR_APP_PORT --reload