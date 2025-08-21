@echo off
REM Pre-commit Hook Uninstallation Script for Product Service (Windows)
REM This script removes all pre-commit security hooks and related files

echo 🗑️ Uninstalling pre-commit security hooks for Product Service...

REM Check if we're in a Git repository
if not exist ".git" (
    echo ERROR: Not in a Git repository. Please run this script from the project root.
    pause
    exit /b 1
)

echo INFO: Working in directory: %CD%

REM Run the bash version of the script using Git Bash
echo INFO: Running uninstall script via Git Bash...

REM Try different possible locations for bash
set BASH_CMD=
if exist "C:\Program Files\Git\bin\bash.exe" (
    set BASH_CMD="C:\Program Files\Git\bin\bash.exe"
) else if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    set BASH_CMD="C:\Program Files (x86)\Git\bin\bash.exe"
) else (
    where bash >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Bash not found. Please install Git for Windows or run the .sh script manually.
        pause
        exit /b 1
    ) else (
        set BASH_CMD=bash
    )
)

REM Execute the bash script
echo INFO: Using bash command: %BASH_CMD%
%BASH_CMD% scripts/uninstall-precommit.sh

if errorlevel 1 (
    echo ERROR: Uninstallation failed
    pause
    exit /b 1
) else (
    echo SUCCESS: Pre-commit hooks uninstalled successfully
    echo.
    echo To reinstall, run: scripts\install-precommit.bat
    pause
    exit /b 0
)
