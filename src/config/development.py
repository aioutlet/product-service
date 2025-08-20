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
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mongodb://admin:admin123@localhost:27018/products_db",  # pragma: allowlist secret
    )
    DATABASE_NAME = os.getenv("DATABASE_NAME", "products_db")

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
