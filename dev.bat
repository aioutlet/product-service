@echo off
:loop
echo.
echo ============================================
echo Starting product service...
echo ============================================
echo.

REM Check if port 8003 is in use and kill the process
echo Checking port 8003...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8003 ^| findstr LISTENING') do (
    echo Port 8003 is in use by PID %%a, killing process...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 1 >nul
)

echo Starting service on port 8003...
python -m uvicorn src.main:app --reload --port 8003

echo.
echo ============================================
echo Service stopped. Press any key to restart or Ctrl+C to exit.
echo ============================================
pause > nul
goto loop
