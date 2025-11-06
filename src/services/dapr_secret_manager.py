"""
Dapr Secret Management Utility - Simplified Version

This module provides a simple way to manage secrets using Dapr's secret stores.
Falls back to environment variables if Dapr is not available.
"""

import os
from typing import Dict, Any, Optional
from dapr.clients import DaprClient

# Import the service's custom logger
from src.core.logger import logger


class DaprSecretManager:
    """Simple secret manager that tries Dapr first, falls back to env vars."""
    
    def __init__(self):
        self.dapr_enabled = os.getenv('DAPR_ENABLED', 'true').lower() == 'true'
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        # Use local secret store for dev, azure keyvault for prod
        if self.environment == 'production':
            self.secret_store_name = 'azure-keyvault-secret-store'
        else:
            self.secret_store_name = 'local-secret-store'
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get a secret, trying Dapr first, then environment variables."""
        
        # If Dapr is disabled, just use environment variables
        if not self.dapr_enabled:
            return os.getenv(secret_name)
        
        # Try Dapr secret store
        try:
            with DaprClient() as client:
                response = client.get_secret(
                    store_name=self.secret_store_name,
                    key=secret_name
                )
                
                # Handle different response types
                if hasattr(response.secret, 'get'):
                    # Dict-like object, try to get the value by key
                    value = response.secret.get(secret_name)
                    if value is not None:
                        return str(value)
                    
                    # If not found by key, try getting first value
                    if response.secret:
                        values = list(response.secret.values())
                        if values:
                            return str(values[0])
                
                elif response.secret:
                    # Direct value
                    return str(response.secret)
                    
                # If we get here, no value was found
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get secret '{secret_name}' from Dapr: {e}")
        
        # Fallback to environment variable
        return os.getenv(secret_name)


# Global instance
secret_manager = DaprSecretManager()


def get_database_config() -> Dict[str, Any]:
    """Get database configuration from secrets or environment variables."""
    
    return {
        'host': secret_manager.get_secret('MONGODB_HOST') or 'localhost',
        'port': int(secret_manager.get_secret('MONGODB_PORT') or '27019'),
        'username': secret_manager.get_secret('MONGO_INITDB_ROOT_USERNAME') or 'admin',
        'password': secret_manager.get_secret('MONGO_INITDB_ROOT_PASSWORD') or 'admin123',
        'database': secret_manager.get_secret('MONGO_INITDB_DATABASE') or 'product_service_db',
        'auth_source': secret_manager.get_secret('MONGODB_AUTH_SOURCE') or 'admin'
    }


def get_jwt_config() -> Dict[str, Any]:
    """Get JWT configuration from secrets or environment variables."""
    
    return {
        'secret': secret_manager.get_secret('JWT_SECRET') or 'default-secret-key',
        'algorithm': secret_manager.get_secret('JWT_ALGORITHM') or 'HS256',
        'expire_minutes': int(secret_manager.get_secret('JWT_EXPIRE_MINUTES') or '480')
    }