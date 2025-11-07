"""
Core configuration and settings for the Product Service
Following FastAPI best practices for configuration management

Note: For sensitive secrets (database credentials, JWT secrets), use:
- from app.services.dapr_secret_manager import get_database_config, get_jwt_config
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration with environment variable support"""
    
    # Service information
    service_name: str = Field(default="product-service", env="NAME")
    service_version: str = Field(default="1.0.0", env="VERSION")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server configuration
    port: int = Field(default=8003, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="console", env="LOG_FORMAT")
    log_to_file: bool = Field(default=True, env="LOG_TO_FILE")
    log_to_console: bool = Field(default=True, env="LOG_TO_CONSOLE")
    
    # Security configuration
    correlation_id_header: str = Field(default="X-Correlation-ID", env="CORRELATION_ID_HEADER")
    
    # Dapr configuration
    dapr_http_port: int = Field(default=3500, env="DAPR_HTTP_PORT")
    dapr_grpc_port: int = Field(default=50001, env="DAPR_GRPC_PORT")
    
    class ConfigDict:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored


# Global config instance
config = Config()