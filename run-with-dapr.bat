@echo off
REM Start Product Service with Dapr sidecar
REM This script runs the FastAPI app with Dapr integration

echo Starting Product Service with Dapr sidecar...
echo.
echo Dapr Configuration:
echo   App ID: product-service
echo   App Port: 8003
echo   Dapr HTTP Port: 3500
echo   Dapr gRPC Port: 50001
echo   Components Path: .dapr/components
echo.

C:\dapr\dapr.exe run ^
  --app-id product-service ^
  --app-port 8003 ^
  --dapr-http-port 3500 ^
  --dapr-grpc-port 50001 ^
  --components-path ./.dapr/components ^
  --log-level info ^
  -- python src/main.py
