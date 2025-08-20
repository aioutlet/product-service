# Configuration Factory for Product Service
import os
from typing import Type


class Config:
    """Base configuration class"""

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = False

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")  # nosec B104
    PORT = int(os.getenv("PORT", 8000))

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "products_db")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_config() -> Type[Config]:
    """
    Get configuration class based on environment
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "development":
        from .development import DevelopmentConfig

        return DevelopmentConfig
    elif env == "production":
        from .production import ProductionConfig

        return ProductionConfig
    elif env == "testing":
        from .testing import TestingConfig

        return TestingConfig
    else:
        # Default to development
        from .development import DevelopmentConfig

        return DevelopmentConfig
