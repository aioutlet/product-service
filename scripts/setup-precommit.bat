@echo off
REM Pre-commit Hook Installation Script for Product Service (Windows)
REM This script sets up comprehensive security scanning hooks

echo.
echo 🔐 Setting up pre-commit security hooks for Product Service...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python first.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo [INFO] Python and pip are available

REM Check if we're in the right directory
if not exist ".pre-commit-config.yaml" (
    echo [ERROR] This script must be run from the product-service directory containing .pre-commit-config.yaml
    pause
    exit /b 1
)

echo [INFO] Found .pre-commit-config.yaml

REM Install pre-commit
echo.
echo === Installing pre-commit ===
pre-commit --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pre-commit...
    pip install pre-commit
) else (
    echo [INFO] pre-commit is already installed
)

REM Install development dependencies
echo.
echo === Installing development dependencies ===
echo [INFO] Installing development dependencies...
pip install -r requirements-dev.txt

REM Install TruffleHog (Windows)
echo.
echo === Installing TruffleHog ===
trufflehog --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing TruffleHog...
    echo [WARNING] Please manually install TruffleHog from: https://github.com/trufflesecurity/trufflehog/releases
    echo [WARNING] Download the Windows binary and add it to your PATH
    pause
) else (
    echo [INFO] TruffleHog is already installed
)

REM Install pre-commit hooks
echo.
echo === Installing Pre-commit Hooks ===
echo [INFO] Installing pre-commit hooks...
pre-commit install

REM Create secrets baseline
echo.
echo === Setting up Secret Detection Baseline ===
if not exist ".secrets.baseline" (
    echo [INFO] Creating secrets baseline...
    detect-secrets scan --baseline .secrets.baseline
    echo [INFO] Created .secrets.baseline - review this file and commit it to track known secrets
) else (
    echo [INFO] Secrets baseline already exists
)

REM Run initial scan
echo.
echo === Running Initial Security Scan ===
echo [INFO] Running pre-commit on all files (this may take a few minutes)...

pre-commit run --all-files
if errorlevel 1 (
    echo [WARNING] Some checks failed. Please review the output above and fix any issues.
    echo [INFO] You can run individual checks with:
    echo   - pre-commit run bandit --all-files
    echo   - pre-commit run detect-secrets --all-files
    echo   - pre-commit run custom-secret-patterns --all-files
) else (
    echo [INFO] All security checks passed! ✅
)

REM Create Git hooks info
echo.
echo === Git Integration ===
echo [INFO] Pre-commit hooks are now installed and will run automatically on:
echo   - git commit (most hooks)
echo   - git push (TODO/FIXME checks)
echo.
echo [INFO] To manually run all hooks: pre-commit run --all-files
echo [INFO] To update hooks: pre-commit autoupdate
echo [INFO] To bypass hooks (NOT recommended): git commit --no-verify

echo.
echo === Setup Complete! ===
echo 🎉 Pre-commit security hooks are now installed!
echo.
echo Next steps:
echo 1. Review and commit .secrets.baseline if it was created
echo 2. Test the hooks: git add . ^&^& git commit -m "test: security hooks"
echo 3. Configure push protection in GitHub repository settings
echo 4. Set up branch protection rules
echo.
echo Security tools installed:
echo ✅ detect-secrets - Secret detection
echo ✅ bandit - Python security linting
echo ✅ safety - Dependency vulnerability scanning
echo ✅ trufflehog - Advanced secret scanning
echo ✅ hadolint - Dockerfile security linting
echo ✅ Custom patterns - Additional secret detection
echo.
echo For more information, see: https://pre-commit.com/

pause
