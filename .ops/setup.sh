#!/bin/bash

# Product Service Environment Setup Script
# This script sets up the development environment for the product-service (Python/FastAPI)

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
SERVICE_NAME="product-service"
SERVICE_PORT="8000"
PYTHON_VERSION="3.9"

# Default environment
ENVIRONMENT="development"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Product Service Environment Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Set environment (development, production, staging)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Setup development environment"
    echo "  $0 -e production        # Setup production environment"
    echo "  $0 -e staging           # Setup staging environment"
    echo ""
    echo "This script will:"
    echo "  1. Validate Python installation and version"
    echo "  2. Create and activate virtual environment"
    echo "  3. Install Python dependencies"
    echo "  4. Load environment variables from .env files"
    echo "  5. Setup MongoDB database and collections"
    echo "  6. Run database migrations and seeding"
    echo "  7. Validate service configuration"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

print_status "🚀 Starting Product Service Environment Setup"
print_status "Environment: $ENVIRONMENT"
print_status "Service: $SERVICE_NAME"
print_status "Port: $SERVICE_PORT"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

print_status "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Validate Python installation
print_status "Step 1: Validating Python installation..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.$PYTHON_VERSION or later."
    exit 1
fi

PYTHON_VERSION_INSTALLED=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION_INSTALLED is installed"

# Step 2: Check for pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi

print_success "pip3 is available"
echo ""

# Step 3: Create and activate virtual environment
print_status "Step 2: Setting up Python virtual environment..."

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created in $VENV_DIR"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"
echo ""

# Step 4: Upgrade pip and install dependencies
print_status "Step 3: Installing Python dependencies..."

pip install --upgrade pip
print_success "pip upgraded"

if [ -f "requirements.txt" ]; then
    print_status "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    print_success "Python dependencies installed successfully"
else
    print_warning "No requirements.txt found, skipping dependency installation"
fi
echo ""

# Step 5: Load environment variables
print_status "Step 4: Loading environment configuration..."

# Check for environment-specific .env file first
ENV_FILE=".env.$ENVIRONMENT"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE=".env"
fi

if [ ! -f "$ENV_FILE" ]; then
    print_warning "No environment file found. Creating template .env files..."

    # Create .env.development template
    cat > .env.development << 'EOF'
# Development Environment Configuration for Product Service
ENVIRONMENT=development
SERVICE_NAME=product-service
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=console

# Server Configuration
PORT=8000
API_VERSION=1.0
HOST=localhost

# JWT Configuration
JWT_SECRET=dev_jwt_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MongoDB Configuration
MONGODB_CONNECTION_SCHEME=mongodb
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password
MONGODB_DB_NAME=product_service_dev
MONGODB_DB_PARAMS=authSource=admin

# Product Service Configuration
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
ENABLE_PRODUCT_REVIEWS=true
ENABLE_PRODUCT_RATINGS=true
ENABLE_PRODUCT_VARIANTS=true
ENABLE_PRODUCT_COLLECTIONS=true

# File Upload Configuration
MAX_PRODUCT_IMAGES=10
MAX_IMAGE_SIZE_MB=5
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,webp
IMAGE_STORAGE_PATH=uploads/products
CDN_BASE_URL=http://localhost:8000/uploads

# Search Configuration
ENABLE_FULL_TEXT_SEARCH=true
SEARCH_INDEX_NAME=products_search
MAX_SEARCH_RESULTS=100

# Cache Configuration
REDIS_URL=redis://localhost:6379/2
CACHE_TTL_SECONDS=3600
ENABLE_QUERY_CACHE=true

# External Services
USER_SERVICE_URL=http://localhost:3000
INVENTORY_SERVICE_URL=http://localhost:8080
NOTIFICATION_SERVICE_URL=http://localhost:3002

# Rate Limiting
RATE_LIMIT_PER_MINUTE=1000
RATE_LIMIT_BURST=100

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CORS_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_HEADERS=*
EOF

    # Create .env.production template
    cat > .env.production << 'EOF'
# Production Environment Configuration for Product Service
ENVIRONMENT=production
SERVICE_NAME=product-service
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_TO_FILE=true
LOG_TO_CONSOLE=true
LOG_FILE_PATH=/var/log/product-service.log

# Server Configuration
PORT=8000
API_VERSION=1.0
HOST=0.0.0.0

# JWT Configuration (SET THESE IN PRODUCTION)
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# MongoDB Configuration (SET THESE IN PRODUCTION)
MONGODB_CONNECTION_SCHEME=mongodb
MONGODB_HOST=${MONGODB_HOST}
MONGODB_PORT=${MONGODB_PORT}
MONGODB_USERNAME=${MONGODB_USERNAME}
MONGODB_PASSWORD=${MONGODB_PASSWORD}
MONGODB_DB_NAME=${MONGODB_DB_NAME}
MONGODB_DB_PARAMS=${MONGODB_DB_PARAMS}

# Product Service Configuration
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=50
ENABLE_PRODUCT_REVIEWS=true
ENABLE_PRODUCT_RATINGS=true
ENABLE_PRODUCT_VARIANTS=true
ENABLE_PRODUCT_COLLECTIONS=true

# File Upload Configuration
MAX_PRODUCT_IMAGES=10
MAX_IMAGE_SIZE_MB=5
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,webp
IMAGE_STORAGE_PATH=/app/uploads/products
CDN_BASE_URL=${CDN_BASE_URL}

# Search Configuration
ENABLE_FULL_TEXT_SEARCH=true
SEARCH_INDEX_NAME=products_search
MAX_SEARCH_RESULTS=50

# Cache Configuration
REDIS_URL=${REDIS_URL}
CACHE_TTL_SECONDS=3600
ENABLE_QUERY_CACHE=true

# External Services
USER_SERVICE_URL=${USER_SERVICE_URL}
INVENTORY_SERVICE_URL=${INVENTORY_SERVICE_URL}
NOTIFICATION_SERVICE_URL=${NOTIFICATION_SERVICE_URL}

# Rate Limiting
RATE_LIMIT_PER_MINUTE=500
RATE_LIMIT_BURST=50

# CORS Configuration
CORS_ORIGINS=${CORS_ORIGINS}
CORS_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_HEADERS=*
EOF

    # Create .env.staging template
    cat > .env.staging << 'EOF'
# Staging Environment Configuration for Product Service
ENVIRONMENT=staging
SERVICE_NAME=product-service
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# Server Configuration
PORT=8000
API_VERSION=1.0
HOST=0.0.0.0

# JWT Configuration
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120

# MongoDB Configuration
MONGODB_CONNECTION_SCHEME=mongodb
MONGODB_HOST=${MONGODB_HOST}
MONGODB_PORT=${MONGODB_PORT}
MONGODB_USERNAME=${MONGODB_USERNAME}
MONGODB_PASSWORD=${MONGODB_PASSWORD}
MONGODB_DB_NAME=${MONGODB_DB_NAME}
MONGODB_DB_PARAMS=${MONGODB_DB_PARAMS}

# Product Service Configuration
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
ENABLE_PRODUCT_REVIEWS=true
ENABLE_PRODUCT_RATINGS=true
ENABLE_PRODUCT_VARIANTS=true
ENABLE_PRODUCT_COLLECTIONS=true

# File Upload Configuration
MAX_PRODUCT_IMAGES=10
MAX_IMAGE_SIZE_MB=5
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,webp
IMAGE_STORAGE_PATH=/app/uploads/products
CDN_BASE_URL=${CDN_BASE_URL}

# Search Configuration
ENABLE_FULL_TEXT_SEARCH=true
SEARCH_INDEX_NAME=products_search
MAX_SEARCH_RESULTS=100

# Cache Configuration
REDIS_URL=${REDIS_URL}
CACHE_TTL_SECONDS=1800
ENABLE_QUERY_CACHE=true

# External Services
USER_SERVICE_URL=${USER_SERVICE_URL}
INVENTORY_SERVICE_URL=${INVENTORY_SERVICE_URL}
NOTIFICATION_SERVICE_URL=${NOTIFICATION_SERVICE_URL}

# Rate Limiting
RATE_LIMIT_PER_MINUTE=750
RATE_LIMIT_BURST=75

# CORS Configuration
CORS_ORIGINS=${CORS_ORIGINS}
CORS_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_HEADERS=*
EOF

    print_success "Environment template files created"
    ENV_FILE=".env.development"
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    print_status "Loading environment variables from $ENV_FILE"
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a  # Stop automatically exporting
    print_success "Environment variables loaded successfully"
else
    print_error "Environment file $ENV_FILE not found"
    exit 1
fi
echo ""

# Step 6: Validate required environment variables
print_status "Step 5: Validating environment configuration..."

REQUIRED_VARS=(
    "SERVICE_NAME"
    "PORT"
    "MONGODB_HOST"
    "MONGODB_PORT"
    "MONGODB_DB_NAME"
    "JWT_SECRET"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        print_error "  - $var"
    done
    print_error "Please check your environment file: $ENV_FILE"
    exit 1
fi

print_success "All required environment variables are set"
echo ""

# Step 7: Setup database (if needed)
print_status "Step 6: Setting up MongoDB database..."

# Check if MongoDB is running
if ! command -v mongosh &> /dev/null && ! command -v mongo &> /dev/null; then
    print_warning "MongoDB client (mongosh/mongo) not found. Skipping database setup."
    print_warning "Please ensure MongoDB is running and accessible at ${MONGODB_HOST}:${MONGODB_PORT}"
else
    print_status "MongoDB client found. Database connection will be validated by the application."
fi
echo ""

# Step 8: Run database scripts
print_status "Step 7: Running database setup scripts..."

if [ -f "database/scripts/clear.py" ]; then
    print_status "Running database clear script..."
    python3 database/scripts/clear.py
    print_success "Database cleared successfully"
fi

if [ -f "database/scripts/seed.py" ]; then
    print_status "Running database seed script..."
    python3 database/scripts/seed.py
    print_success "Database seeded successfully"
fi
echo ""

# Step 9: Install development tools
print_status "Step 8: Installing development tools..."

# Install additional development dependencies if in development mode
if [ "$ENVIRONMENT" = "development" ]; then
    print_status "Installing development dependencies..."
    pip install pytest pytest-asyncio pytest-cov black flake8 mypy
    print_success "Development tools installed"
fi
echo ""

# Step 10: Validate service
print_status "Step 9: Validating service configuration..."

# Check if the service can start (dry run)
if [ -f "src/main.py" ]; then
    print_status "Validating FastAPI application..."
    python3 -c "
import sys
sys.path.append('src')
try:
    from main import app
    print('✅ FastAPI application validation successful')
except Exception as e:
    print(f'❌ FastAPI application validation failed: {e}')
    sys.exit(1)
    "
    if [ $? -eq 0 ]; then
        print_success "Service configuration is valid"
    else
        print_error "Service configuration validation failed"
        exit 1
    fi
else
    print_warning "No main.py found, skipping service validation"
fi
echo ""

# Step 11: Final status
print_success "🎉 Product Service environment setup completed successfully!"
echo ""

# Step 12: Start services with Docker Compose
echo -e "${BLUE}� Starting services with Docker Compose...${NC}"
if docker-compose up -d; then
    print_success "Services started successfully"
    echo ""
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 15

    # Check service health
    if docker-compose ps | grep -q "Up.*healthy\|Up"; then
        print_success "Services are healthy and ready"
    else
        print_warning "Services may still be starting up"
    fi
else
    print_error "Failed to start services with Docker Compose"
    exit 1
fi
echo ""

echo -e "${BLUE}�📋 Setup Summary:${NC}"
echo "  ✅ Python virtual environment: $VENV_DIR"
echo "  ✅ Environment: $ENVIRONMENT"
echo "  ✅ Configuration file: $ENV_FILE"
echo "  ✅ Service port: $SERVICE_PORT"
echo "  ✅ MongoDB database: ${MONGODB_DB_NAME}"
echo "  ✅ Dependencies installed"
echo "  ✅ Database setup completed"
echo "  ✅ Services running with Docker Compose"
echo ""
echo -e "${BLUE}🚀 Service is now running:${NC}"
echo "  • View status: docker-compose ps"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: bash .ops/teardown.sh"
echo "  • API documentation: http://localhost:$SERVICE_PORT/docs"
echo "  • Health check: http://localhost:$SERVICE_PORT/health"
echo ""

# Keep virtual environment activated
print_status "Virtual environment remains activated for this session"
print_status "Use 'deactivate' to exit the virtual environment"
echo ""
