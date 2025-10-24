# Development Configuration for Product Service
import os


class DevelopmentConfig:
    """Development configuration settings"""

    # Environment
    ENVIRONMENT = "development"
    DEBUG = True

    # Server
    HOST = "0.0.0.0"  # nosec B104
    PORT = 8000

    # Database Configuration - MongoDB
    # Construct MongoDB URI from environment variables
    _mongo_host = os.getenv("MONGODB_HOST", "localhost")
    _mongo_port = os.getenv("MONGODB_PORT", "27017")
    _mongo_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    _mongo_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    _mongo_database = os.getenv("MONGO_INITDB_DATABASE", "products_db")
    _mongo_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    if _mongo_username and _mongo_password:
        DATABASE_URL = f"mongodb://{_mongo_username}:{_mongo_password}@{_mongo_host}:{_mongo_port}/{_mongo_database}?authSource={_mongo_auth_source}"
    else:
        DATABASE_URL = f"mongodb://{_mongo_host}:{_mongo_port}/{_mongo_database}"
    
    DATABASE_NAME = _mongo_database

    # Redis Configuration (for caching)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
    ]

    # External Services
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:4000")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:3002")
    ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:3005")
    INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8080")
    AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://localhost:3009")

    # Logging
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_TO_FILE = False
    LOG_TO_CONSOLE = True

    # Product Configuration
    MAX_PRODUCTS_PER_PAGE = 50
    DEFAULT_PRODUCTS_PER_PAGE = 20
    ENABLE_PRODUCT_SEARCH = True
    ENABLE_PRODUCT_RECOMMENDATIONS = True

    # File Upload
    UPLOAD_FOLDER = "uploads/products"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_PER_MINUTE = 100

    # Health Check
    HEALTH_CHECK_ENABLED = True

    # Monitoring
    METRICS_ENABLED = True
    PROMETHEUS_ENABLED = False
