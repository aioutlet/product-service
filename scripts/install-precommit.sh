#!/bin/bash

# Pre-commit Hook Installation Script for Product Service
# This script sets up comprehensive security scanning hooks

set -e

echo "🔐 Setting up pre-commit security hooks for Product Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if Python is installed
print_header "Checking Prerequisites"

# Detect Python command (python3 on Linux/macOS, python on Windows)
PYTHON_CMD=""
PIP_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    # Check if it's Python 3
    PYTHON_VERSION=$(python -c "import sys; print(sys.version_info[0])")
    if [ "$PYTHON_VERSION" = "3" ]; then
        PYTHON_CMD="python"
        PIP_CMD="pip"
    else
        print_error "Python 3 is required, but only Python 2 was found."
        exit 1
    fi
else
    print_error "Python is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is available
if ! command -v $PIP_CMD &> /dev/null; then
    print_error "$PIP_CMD is not installed. Please install pip first."
    exit 1
fi

print_status "Python 3 and pip are available (using commands: $PYTHON_CMD, $PIP_CMD)"

# Add Python user scripts to PATH if needed
PYTHON_USER_SCRIPTS_PATH=""
if [ "$PYTHON_CMD" = "python" ]; then
    # Windows Python - get user scripts directory
    PYTHON_USER_SCRIPTS_PATH=$($PYTHON_CMD -c "import site; print(site.getusersitepackages().replace('site-packages', 'Scripts'))" 2>/dev/null)
    if [ -d "$PYTHON_USER_SCRIPTS_PATH" ]; then
        export PATH="$PYTHON_USER_SCRIPTS_PATH:$PATH"
        print_status "Added Python user scripts directory to PATH: $PYTHON_USER_SCRIPTS_PATH"
    fi
elif [ "$PYTHON_CMD" = "python3" ]; then
    # Linux/macOS - check for ~/.local/bin
    if [ -d "$HOME/.local/bin" ]; then
        export PATH="$HOME/.local/bin:$PATH"
        print_status "Added ~/.local/bin to PATH"
    fi
fi

# Check if we're in the right directory
if [ ! -f ".pre-commit-config.yaml" ]; then
    print_error "This script must be run from the product-service directory containing .pre-commit-config.yaml"
    exit 1
fi

print_status "Found .pre-commit-config.yaml"

# Install pre-commit
print_header "Installing pre-commit"
if ! command -v pre-commit &> /dev/null; then
    print_status "Installing pre-commit..."
    $PIP_CMD install pre-commit
else
    print_status "pre-commit is already installed"
fi

# Create requirements-dev.txt for development dependencies
print_header "Setting up development dependencies"
cat > requirements-dev.txt << EOF
# Development and security dependencies
pre-commit>=3.6.0
bandit>=1.7.5
safety>=2.3.5
detect-secrets>=1.4.0
black>=23.12.0
isort>=5.13.0
flake8>=7.0.0
yamllint>=1.35.0
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
EOF

print_status "Created requirements-dev.txt with security tools"

# Install development dependencies
print_status "Installing development dependencies..."
$PIP_CMD install -r requirements-dev.txt

# Install TruffleHog (binary installation)
print_header "Installing TruffleHog"
if ! command -v trufflehog &> /dev/null; then
    print_status "Installing TruffleHog..."

    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)

    # Handle Windows/MSYS/Git Bash environment
    case $OS in
        mingw*|msys*|cygwin*)
            OS="windows"
            ;;
        *)
            ;;
    esac

    case $ARCH in
        x86_64) ARCH="amd64" ;;
        arm64) ARCH="arm64" ;;
        aarch64) ARCH="arm64" ;;
        *) print_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac

    # Download and install TruffleHog
    TRUFFLEHOG_VERSION="3.63.2"

    if [ "$OS" = "windows" ]; then
        DOWNLOAD_URL="https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION}_windows_${ARCH}.tar.gz"
        print_status "Downloading TruffleHog for Windows from $DOWNLOAD_URL"
        curl -L "$DOWNLOAD_URL" | tar -xz

        # Create local bin directory and move executable
        mkdir -p ~/.local/bin
        mv trufflehog.exe ~/.local/bin/ 2>/dev/null || mv trufflehog ~/.local/bin/trufflehog.exe
        print_warning "TruffleHog installed to ~/.local/bin/ - make sure this is in your PATH"
        print_warning "You may need to restart your terminal or run: export PATH=~/.local/bin:\$PATH"
    else
        DOWNLOAD_URL="https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION}_${OS}_${ARCH}.tar.gz"
        print_status "Downloading TruffleHog from $DOWNLOAD_URL"
        curl -L "$DOWNLOAD_URL" | tar -xz

        # Move to PATH (or local bin directory)
        if [ -w "/usr/local/bin" ]; then
            sudo mv trufflehog /usr/local/bin/
        else
            mkdir -p ~/.local/bin
            mv trufflehog ~/.local/bin/
            print_warning "TruffleHog installed to ~/.local/bin/ - make sure this is in your PATH"
        fi
    fi

    print_status "TruffleHog installed successfully"
else
    print_status "TruffleHog is already installed"
fi

# Install hadolint (Dockerfile linter)
print_header "Installing hadolint"
if ! command -v hadolint &> /dev/null; then
    print_status "Installing hadolint..."

    # Detect OS and architecture for hadolint
    case $OS in
        "windows")
            # For Windows, we'll use Docker or skip with warning
            if command -v docker &> /dev/null; then
                print_status "Docker detected. hadolint will run via Docker."
                # Create a wrapper script for hadolint
                cat > ~/.local/bin/hadolint << 'EOF'
#!/bin/bash
docker run --rm -i hadolint/hadolint:latest "$@"
EOF
                chmod +x ~/.local/bin/hadolint
                print_status "hadolint wrapper created at ~/.local/bin/hadolint"
            else
                print_warning "hadolint installation requires Docker on Windows. Skipping hadolint installation."
                print_warning "To install hadolint manually, visit: https://github.com/hadolint/hadolint"
            fi
            ;;
        "linux")
            # Download hadolint binary for Linux
            HADOLINT_VERSION="v2.12.0"
            wget -q -O hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-x86_64"
            chmod +x hadolint
            if [ -d ~/.local/bin ]; then
                mv hadolint ~/.local/bin/
                print_status "hadolint installed to ~/.local/bin/"
            else
                mkdir -p ~/.local/bin
                mv hadolint ~/.local/bin/
                print_warning "hadolint installed to ~/.local/bin/ - make sure this is in your PATH"
            fi
            ;;
        "darwin")
            # Use Homebrew on macOS if available, otherwise manual download
            if command -v brew &> /dev/null; then
                brew install hadolint
                print_status "hadolint installed via Homebrew"
            else
                HADOLINT_VERSION="v2.12.0"
                curl -sL -o hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Darwin-x86_64"
                chmod +x hadolint
                if [ -d ~/.local/bin ]; then
                    mv hadolint ~/.local/bin/
                    print_status "hadolint installed to ~/.local/bin/"
                else
                    mkdir -p ~/.local/bin
                    mv hadolint ~/.local/bin/
                    print_warning "hadolint installed to ~/.local/bin/ - make sure this is in your PATH"
                fi
            fi
            ;;
        *)
            print_warning "Unsupported OS for automatic hadolint installation: $OS"
            print_warning "Please install hadolint manually: https://github.com/hadolint/hadolint"
            ;;
    esac
else
    print_status "hadolint is already installed"
fi

# Install pre-commit hooks
print_header "Installing Pre-commit Hooks"

# Find pre-commit command
PRECOMMIT_CMD=""
if command -v pre-commit &> /dev/null; then
    PRECOMMIT_CMD="pre-commit"
elif [ -n "$PYTHON_USER_SCRIPTS_PATH" ] && [ -f "$PYTHON_USER_SCRIPTS_PATH/pre-commit" ]; then
    PRECOMMIT_CMD="$PYTHON_USER_SCRIPTS_PATH/pre-commit"
elif [ -n "$PYTHON_USER_SCRIPTS_PATH" ] && [ -f "$PYTHON_USER_SCRIPTS_PATH/pre-commit.exe" ]; then
    PRECOMMIT_CMD="$PYTHON_USER_SCRIPTS_PATH/pre-commit.exe"
elif [ -f "$HOME/.local/bin/pre-commit" ]; then
    PRECOMMIT_CMD="$HOME/.local/bin/pre-commit"
else
    print_error "pre-commit command not found after installation. Please check your PATH."
    print_warning "You may need to restart your terminal or add Python scripts directory to PATH"
    exit 1
fi

print_status "Installing pre-commit hooks using: $PRECOMMIT_CMD"
$PRECOMMIT_CMD install

# Create secrets baseline
print_header "Setting up Secret Detection Baseline"

# Find detect-secrets command
DETECT_SECRETS_CMD=""
if command -v detect-secrets &> /dev/null; then
    DETECT_SECRETS_CMD="detect-secrets"
elif [ -n "$PYTHON_USER_SCRIPTS_PATH" ] && [ -f "$PYTHON_USER_SCRIPTS_PATH/detect-secrets" ]; then
    DETECT_SECRETS_CMD="$PYTHON_USER_SCRIPTS_PATH/detect-secrets"
elif [ -n "$PYTHON_USER_SCRIPTS_PATH" ] && [ -f "$PYTHON_USER_SCRIPTS_PATH/detect-secrets.exe" ]; then
    DETECT_SECRETS_CMD="$PYTHON_USER_SCRIPTS_PATH/detect-secrets.exe"
elif [ -f "$HOME/.local/bin/detect-secrets" ]; then
    DETECT_SECRETS_CMD="$HOME/.local/bin/detect-secrets"
else
    print_error "detect-secrets command not found after installation."
    DETECT_SECRETS_CMD="$PYTHON_CMD -m detect_secrets"
    print_status "Trying to use: $DETECT_SECRETS_CMD"
fi

if [ ! -f ".secrets.baseline" ]; then
    print_status "Creating secrets baseline using: $DETECT_SECRETS_CMD"
    $DETECT_SECRETS_CMD scan > .secrets.baseline
    print_status "Created .secrets.baseline - review this file and commit it to track known secrets"
else
    print_status "Secrets baseline already exists"
fi

# Run initial scan
print_header "Running Initial Security Scan"
print_status "Running pre-commit on all files (this may take a few minutes)..."

if $PRECOMMIT_CMD run --all-files; then
    print_status "All security checks passed! ✅"
else
    print_warning "Some checks failed. Please review the output above and fix any issues."
    print_status "You can run individual checks with:"
    echo "  - $PRECOMMIT_CMD run bandit --all-files"
    echo "  - $PRECOMMIT_CMD run detect-secrets --all-files"
    echo "  - $PRECOMMIT_CMD run trufflehog --all-files"
    echo "  - $PRECOMMIT_CMD run custom-secret-patterns --all-files"
fi

# Create Git hooks info
print_header "Git Integration"
print_status "Pre-commit hooks are now installed and will run automatically on:"
echo "  - git commit (most hooks)"
echo "  - git push (TODO/FIXME checks)"

print_status "To manually run all hooks: $PRECOMMIT_CMD run --all-files"
print_status "To update hooks: $PRECOMMIT_CMD autoupdate"
print_status "To bypass hooks (NOT recommended): git commit --no-verify"

# Create .gitignore entries if needed
print_header "Updating .gitignore"
if [ -f ".gitignore" ]; then
    # Add entries if they don't exist
    grep -q "\.secrets\.baseline" .gitignore || echo ".secrets.baseline" >> .gitignore
    grep -q "requirements-dev\.txt" .gitignore || echo "!requirements-dev.txt" >> .gitignore
    print_status "Updated .gitignore with security tool entries"
else
    print_warning ".gitignore not found - consider creating one"
fi

print_header "Setup Complete!"
echo -e "${GREEN}🎉 Pre-commit security hooks are now installed!${NC}"
echo ""
echo "Next steps:"
echo "1. Review and commit .secrets.baseline if it was created"
echo "2. Test the hooks: git add . && git commit -m 'test: security hooks'"
echo "3. Configure push protection in GitHub repository settings"
echo "4. Set up branch protection rules"
echo ""
echo "Security tools installed:"
echo "✅ detect-secrets - Secret detection"
echo "✅ bandit - Python security linting"
echo "✅ safety - Dependency vulnerability scanning"
echo "✅ trufflehog - Advanced secret scanning"
echo "✅ hadolint - Dockerfile security linting"
echo "✅ Custom patterns - Additional secret detection"
echo ""
echo "For more information, see: https://pre-commit.com/"
