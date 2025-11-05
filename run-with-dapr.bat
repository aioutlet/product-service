@echo off
REM Dapr run script for Product Service (Windows)

echo 🚀 Starting Product Service with Dapr...

REM Set Dapr app configuration
set DAPR_APP_ID=product-service
set DAPR_HTTP_PORT=3500
set DAPR_GRPC_PORT=50001
set DAPR_APP_PORT=8003

echo 📦 Dapr Configuration:
echo    App ID: %DAPR_APP_ID%
echo    HTTP Port: %DAPR_HTTP_PORT%
echo    gRPC Port: %DAPR_GRPC_PORT%
echo    App Port: %DAPR_APP_PORT%
echo.

REM Check if Dapr is installed
where dapr >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Dapr CLI is not installed!
    echo Please install Dapr CLI: https://docs.dapr.io/getting-started/install-dapr-cli/
    pause
    exit /b 1
)

echo 🔍 Checking dependencies...

REM Check if Redis is available (we'll start it with Docker if needed)
docker ps --filter "name=dapr-redis" --format "table {{.Names}}" | findstr dapr-redis >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 🐳 Starting Redis container for Dapr...
    docker run -d --name dapr-redis -p 6379:6379 redis:alpine
    timeout 3 >nul
    echo ✅ Redis started
) else (
    echo ✅ Redis container is already running
)

echo.
echo 🏁 Starting Product Service with Dapr sidecar...
echo.

REM Start the product service with Dapr
dapr run ^
  --app-id %DAPR_APP_ID% ^
  --app-port %DAPR_APP_PORT% ^
  --dapr-http-port %DAPR_HTTP_PORT% ^
  --dapr-grpc-port %DAPR_GRPC_PORT% ^
  --components-path .dapr/components ^
  -- python -m uvicorn src.main:app --host 0.0.0.0 --port %DAPR_APP_PORT% --reload
