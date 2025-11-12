@echo off
REM Dapr run script for Product Service with debugpy for VS Code debugging

echo Starting Product Service with Dapr (DEBUG MODE)...
echo.

REM Set Dapr app configuration
set DAPR_APP_ID=product-service
set DAPR_HTTP_PORT=3501
set DAPR_GRPC_PORT=50001
set DAPR_APP_PORT=1001

echo Dapr Configuration:
echo    App ID: %DAPR_APP_ID%
echo    HTTP Port: %DAPR_HTTP_PORT%
echo    gRPC Port: %DAPR_GRPC_PORT%
echo    App Port: %DAPR_APP_PORT%
echo    Debug Port: 5678
echo.

echo Starting Product Service with Dapr sidecar in DEBUG mode...
echo VS Code will be able to attach to debugpy on port 5678
echo.

dapr run ^
  --app-id %DAPR_APP_ID% ^
  --app-port %DAPR_APP_PORT% ^
  --dapr-http-port %DAPR_HTTP_PORT% ^
  --dapr-grpc-port %DAPR_GRPC_PORT% ^
  --resources-path .dapr/components ^
  --config .dapr/config.yaml ^
  --placement-host-address "" ^
  --log-level warn ^
  -- python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn main:app --host 0.0.0.0 --port %DAPR_APP_PORT% --reload --reload-include *.py
