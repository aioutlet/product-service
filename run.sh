#!/usr/bin/env bash
# Run Product Service directly (without Dapr)
# Usage: ./run.sh

echo -e "\033[0;32mStarting Product Service (Direct mode - no Dapr)...\033[0m"
echo -e "\033[0;36mService will be available at: http://localhost:1001\033[0m"
echo -e "\033[0;36mAPI documentation: http://localhost:1001/docs\033[0m"
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 1001 --reload
