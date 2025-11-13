#!/usr/bin/env pwsh
# Run Product Service with Dapr sidecar
# Usage: .\run.ps1

Write-Host "Starting Product Service with Dapr..." -ForegroundColor Green
Write-Host "Service will be available at: http://localhost:1001" -ForegroundColor Cyan
Write-Host "API documentation: http://localhost:1001/docs" -ForegroundColor Cyan
Write-Host "Dapr HTTP endpoint: http://localhost:3501" -ForegroundColor Cyan
Write-Host "Dapr gRPC endpoint: localhost:50001" -ForegroundColor Cyan
Write-Host ""

dapr run `
  --app-id product-service `
  --app-port 1001 `
  --dapr-http-port 3501 `
  --dapr-grpc-port 50001 `
  --resources-path .dapr/components `
  --config .dapr/config.yaml `
  --log-level warn `
  -- python -m uvicorn main:app --host 0.0.0.0 --port 1001 --reload
