#!/bin/bash
# Test Dapr publisher without running full service
# This runs just the publisher test with a temporary Dapr sidecar

echo "Starting Dapr sidecar for testing..."
/c/dapr/dapr.exe run \
  --app-id product-service-test \
  --dapr-http-port 3500 \
  --dapr-grpc-port 50001 \
  --components-path ./.dapr/components \
  --log-level info \
  -- python src/test_dapr_publisher.py
