#!/bin/bash

# Pre-commit Hook Uninstallation Script for Product Service
# This script removes all pre-commit security hooks and related files

set -e

echo "🗑️ Uninstalling pre-commit security hooks for Product Service..."

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

# Check if we're in a Git repository
if [ ! -d ".git" ]; then
    print_error "Not in a Git repository. Please run this script from the project root."
    exit 1
fi

# Get project root directory
PROJECT_ROOT=$(pwd)
print_status "Working in directory: $PROJECT_ROOT"

# Function to safely remove file
safe_remove() {
    local file="$1"
    if [ -f "$file" ]; then
        print_status "Removing $file"
        rm -f "$file"
    else
        print_status "File $file does not exist (already removed)"
    fi
}

# Function to safely remove directory
safe_remove_dir() {
    local dir="$1"
    if [ -d "$dir" ]; then
        print_status "Removing directory $dir"
        rm -rf "$dir"
    else
        print_status "Directory $dir does not exist (already removed)"
    fi
}

print_header "Uninstalling Pre-commit Hooks"

# Detect Python command (python3 on Linux/macOS, python on Windows)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_warning "Python not found. Some cleanup may be incomplete."
fi

# Find pre-commit command
PRECOMMIT_CMD=""
if command -v pre-commit &> /dev/null; then
    PRECOMMIT_CMD="pre-commit"
elif [ -n "$PYTHON_CMD" ]; then
    PRECOMMIT_CMD="$PYTHON_CMD -m pre_commit"
fi

# Uninstall pre-commit hooks
if [ -n "$PRECOMMIT_CMD" ]; then
    print_status "Uninstalling pre-commit hooks..."
    if $PRECOMMIT_CMD uninstall; then
        print_status "Pre-commit hooks uninstalled successfully"
    else
        print_warning "Failed to uninstall pre-commit hooks or they were not installed"
    fi
else
    print_warning "Pre-commit command not found, skipping hook uninstallation"
fi

print_header "Removing Configuration Files"

# Remove pre-commit configuration files
safe_remove ".pre-commit-config.yaml"
safe_remove ".pre-commit-hooks.yaml"

# Remove secrets detection files
safe_remove ".secrets.baseline"

# Remove development requirements
safe_remove "requirements-dev.txt"

# Remove pre-commit cache
safe_remove_dir ".pre-commit"

print_header "Cleaning Git Hooks Directory"

# Remove pre-commit related hooks from .git/hooks/
if [ -d ".git/hooks" ]; then
    print_status "Checking Git hooks directory..."
    
    # List of hook files that might contain pre-commit
    for hook in pre-commit pre-push pre-receive pre-merge-commit prepare-commit-msg commit-msg post-commit post-merge; do
        hook_file=".git/hooks/$hook"
        if [ -f "$hook_file" ]; then
            # Check if the hook file contains pre-commit references
            if grep -q "pre-commit" "$hook_file" 2>/dev/null; then
                print_status "Removing pre-commit hook: $hook_file"
                rm -f "$hook_file"
            fi
        fi
    done
    
    print_status "Git hooks cleanup completed"
fi

print_header "Removing Development Tools"

# Ask user if they want to uninstall Python packages
echo ""
print_warning "Do you want to uninstall the Python development packages?"
print_status "This will remove: pre-commit, bandit, safety, detect-secrets, black, isort, flake8, yamllint, pytest"
echo -n "Uninstall Python packages? (y/N): "
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    if [ -n "$PYTHON_CMD" ]; then
        print_status "Uninstalling Python development packages..."
        
        # List of packages to uninstall
        packages=(
            "pre-commit"
            "bandit"
            "safety"
            "detect-secrets"
            "black"
            "isort"
            "flake8"
            "yamllint"
            "pytest"
            "pytest-cov"
            "pytest-mock"
        )
        
        for package in "${packages[@]}"; do
            print_status "Uninstalling $package..."
            if $PYTHON_CMD -m pip uninstall -y "$package" 2>/dev/null; then
                print_status "Uninstalled $package"
            else
                print_status "$package was not installed or already removed"
            fi
        done
        
        print_status "Python packages uninstalled"
    else
        print_warning "Python not found, cannot uninstall packages"
    fi
else
    print_status "Keeping Python packages installed"
fi

print_header "Removing Binary Tools"

# Ask user if they want to remove binary tools
echo ""
print_warning "Do you want to remove binary security tools?"
print_status "This will remove: trufflehog, hadolint (if installed locally)"
echo -n "Remove binary tools? (y/N): "
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    print_status "Removing binary security tools..."
    
    # Remove TruffleHog
    for location in "/usr/local/bin/trufflehog" "$HOME/.local/bin/trufflehog" "$HOME/.local/bin/trufflehog.exe"; do
        if [ -f "$location" ]; then
            print_status "Removing TruffleHog from $location"
            rm -f "$location"
        fi
    done
    
    # Remove hadolint
    for location in "/usr/local/bin/hadolint" "$HOME/.local/bin/hadolint"; do
        if [ -f "$location" ]; then
            print_status "Removing hadolint from $location"
            rm -f "$location"
        fi
    done
    
    print_status "Binary tools removed"
else
    print_status "Keeping binary tools installed"
fi

print_header "Cleaning .gitignore"

# Remove pre-commit related entries from .gitignore
if [ -f ".gitignore" ]; then
    print_status "Cleaning up .gitignore..."
    
    # Create temporary file
    temp_file=$(mktemp)
    
    # Remove lines related to pre-commit tools
    grep -v -E "^\.secrets\.baseline$|^!requirements-dev\.txt$|^\.pre-commit$" .gitignore > "$temp_file" 2>/dev/null || true
    
    # Replace .gitignore if changes were made
    if ! cmp -s .gitignore "$temp_file"; then
        mv "$temp_file" .gitignore
        print_status ".gitignore cleaned up"
    else
        rm -f "$temp_file"
        print_status ".gitignore unchanged"
    fi
else
    print_status "No .gitignore file found"
fi

print_header "Verification"

# Verify uninstallation
print_status "Verifying uninstallation..."

uninstall_issues=()

# Check for remaining files
remaining_files=(
    ".pre-commit-config.yaml"
    ".secrets.baseline" 
    "requirements-dev.txt"
    ".pre-commit"
)

for file in "${remaining_files[@]}"; do
    if [ -e "$file" ]; then
        uninstall_issues+=("$file still exists")
    fi
done

# Check Git hooks
if [ -d ".git/hooks" ]; then
    for hook in .git/hooks/*; do
        if [ -f "$hook" ] && grep -q "pre-commit" "$hook" 2>/dev/null; then
            uninstall_issues+=("Git hook $(basename "$hook") still contains pre-commit references")
        fi
    done
fi

if [ ${#uninstall_issues[@]} -eq 0 ]; then
    print_status "✅ Uninstallation verification passed"
else
    print_warning "⚠️ Some issues found during verification:"
    for issue in "${uninstall_issues[@]}"; do
        print_warning "  - $issue"
    done
fi

print_header "Uninstallation Complete!"

echo -e "${GREEN}🎉 Pre-commit security hooks have been uninstalled!${NC}"
echo ""
echo "What was removed:"
echo "✅ Pre-commit Git hooks"
echo "✅ Configuration files (.pre-commit-config.yaml, .secrets.baseline)"
echo "✅ Cache directories (.pre-commit/)"
echo "✅ Development requirements file"
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✅ Python security packages"
    echo "✅ Binary security tools"
fi
echo ""
echo "Your repository is now clean of pre-commit hooks."
echo ""
echo "Notes:"
echo "- Your Git history and commits are unchanged"
echo "- Any committed configuration files remain in Git history"
echo "- You can reinstall hooks anytime with: bash scripts/install-precommit.sh"
echo ""
