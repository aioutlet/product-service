#!/bin/bash
# Dapr run script for Product Service

echo "🚀 Starting Product Service with Dapr..."

# Set Dapr app configuration
export DAPR_APP_ID=product-service
export DAPR_HTTP_PORT=3501
export DAPR_GRPC_PORT=50001
export DAPR_APP_PORT=1001

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

echo "🔍 Checking dependencies..."

# Check if RabbitMQ is available
if ! docker ps --filter "name=rabbitmq-message-broker" --format "table {{.Names}}" | grep -q rabbitmq-message-broker; then
    echo "⚠️ RabbitMQ container is not running!"
    echo "Please start RabbitMQ: docker-compose -f scripts/docker-compose/docker-compose.yml up -d rabbitmq"
    exit 1
else
    echo "✅ RabbitMQ container is running"
fi

echo ""
echo "🏁 Starting Product Service with Dapr sidecar..."
echo ""

# Start the product service with Dapr
dapr run \
  --app-id $DAPR_APP_ID \
  --app-port $DAPR_APP_PORT \
  --dapr-http-port $DAPR_HTTP_PORT \
  --dapr-grpc-port $DAPR_GRPC_PORT \
  --resources-path .dapr/components \
  --config .dapr/config.yaml \
  --placement-host-address "" \
  --log-level warn \
  -- python -m uvicorn main:app --host 0.0.0.0 --port $DAPR_APP_PORT --reload --reload-include '*.py'