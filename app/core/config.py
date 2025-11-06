"""
Core configuration and settings for the Product Service
Following FastAPI best practices for configuration management
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration with environment variable support"""
    
    # Service information
    service_name: str = Field(default="product-service", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server configuration
    port: int = Field(default=8003, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    
    # Database configuration
    mongodb_host: str = Field(default="localhost", env="MONGODB_HOST")
    mongodb_port: int = Field(default=27019, env="MONGODB_PORT")
    mongodb_username: Optional[str] = Field(default=None, env="MONGODB_USERNAME")
    mongodb_password: Optional[str] = Field(default=None, env="MONGODB_PASSWORD")
    mongodb_database: str = Field(default="productdb", env="MONGODB_DATABASE")
    
    @property
    def mongodb_url(self) -> str:
        """Construct MongoDB connection URL"""
        if self.mongodb_username and self.mongodb_password:
            return f"mongodb://{self.mongodb_username}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
    
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
    
    # JWT Authentication configuration
    jwt_secret: str = Field(default="your_jwt_secret_key", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration: int = Field(default=3600, env="JWT_EXPIRATION")  # seconds
    
    class ConfigDict:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored


# Global config instance
config = Config()