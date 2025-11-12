@echo off
echo Stopping product service on port 1001...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1001 ^| findstr LISTENING') do (
    echo Killing process with PID %%a...
    taskkill /PID %%a /F
)

echo Done.
