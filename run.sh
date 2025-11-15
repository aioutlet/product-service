#!/usr/bin/env bash
# Run Product Service with Dapr sidecar
# Usage: ./run.sh

echo -e "\033[0;32mStarting Product Service with Dapr...\033[0m"
echo -e "\033[0;36mService will be available at: http://localhost:1001\033[0m"
echo -e "\033[0;36mAPI documentation: http://localhost:1001/docs\033[0m"
echo -e "\033[0;36mDapr HTTP endpoint: http://localhost:3501\033[0m"
echo -e "\033[0;36mDapr gRPC endpoint: localhost:50001\033[0m"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

dapr run \
  --app-id product-service \
  --app-port 1001 \
  --dapr-http-port 3501 \
  --dapr-grpc-port 50001 \
  --resources-path "$SCRIPT_DIR/.dapr/components" \
  --config "$SCRIPT_DIR/.dapr/config.yaml" \
  --log-level warn \
  -- python -m uvicorn main:app --host 0.0.0.0 --port 1001 --reload --reload-delay 2
