#!/usr/bin/env pwsh
# Run Product Service directly (without Dapr)
# Usage: .\run.ps1

Write-Host "Starting Product Service (Direct mode - no Dapr)..." -ForegroundColor Green
Write-Host "Service will be available at: http://localhost:1001" -ForegroundColor Cyan
Write-Host "API documentation: http://localhost:1001/docs" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn main:app --host 0.0.0.0 --port 1001 --reload
