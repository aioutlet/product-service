#!/bin/bash

echo ""
echo "============================================"
echo "Starting Product Service (WITHOUT Dapr)"
echo "============================================"
echo "Mode: Local Development"
echo "Configuration: .env file"
echo "Service URL: http://localhost:1001"
echo "============================================"
echo ""

# Check if port 1001 is in use and kill the process
echo "Checking port 1001..."
PID=$(lsof -ti:1001)
if [ ! -z "$PID" ]; then
    echo "Port 1001 is in use by PID $PID, killing process..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

echo "Starting service on port 1001..."
echo "Press Ctrl+C to stop the service"
echo ""
echo "Note: To run WITH Dapr features, use run-with-dapr.sh instead"
echo ""

python -m uvicorn main:app --reload --port 1001

echo ""
echo "Service stopped."
