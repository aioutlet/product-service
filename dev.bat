@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo Starting Product Service (WITHOUT Dapr)
echo ============================================
echo Mode: Local Development
echo Configuration: .env file
echo Service URL: http://localhost:1001
echo ============================================
echo.

REM Check if port 1001 is in use and kill the process
echo Checking port 1001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1001 ^| findstr LISTENING') do (
    echo Port 1001 is in use by PID %%a, killing process...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 1 >nul
)

echo Starting service on port 1001...
echo Press Ctrl+C to stop the service
echo.
echo Note: To run WITH Dapr features, use run-with-dapr.bat instead
echo.
python -m uvicorn main:app --reload --port 1001

echo.
echo Service stopped.
exit /b
