"""
Dapr Secret Management Service
Provides secret management using Dapr's secret store building block.
Falls back to environment variables if Dapr is not available.
"""

import os
from typing import Dict, Any, Optional

try:
    from dapr.clients import DaprClient
    DAPR_AVAILABLE = True
except ImportError:
    DAPR_AVAILABLE = False

from app.core.logger import logger
from app.core.config import config


class DaprSecretManager:
    """
    Secret manager that uses Dapr secret store building block.
    Automatically falls back to environment variables if Dapr is unavailable.
    """
    
    def __init__(self):
        self.dapr_enabled = os.getenv('DAPR_ENABLED', 'true').lower() == 'true'
        self.environment = config.environment
        
        # Use appropriate secret store based on environment
        if self.environment == 'production':
            self.secret_store_name = 'azure-keyvault-secret-store'
        else:
            self.secret_store_name = 'local-secret-store'
        
        logger.info(
            f"Secret manager initialized",
            metadata={
                "event": "secret_manager_init",
                "dapr_enabled": self.dapr_enabled and DAPR_AVAILABLE,
                "environment": self.environment,
                "secret_store": self.secret_store_name
            }
        )
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get a secret value.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Secret value as string, or None if not found
            
        Priority:
            1. Dapr secret store (if enabled and available)
            2. Environment variable (fallback)
        """
        # If Dapr is disabled or not available, use environment variables
        if not self.dapr_enabled or not DAPR_AVAILABLE:
            value = os.getenv(secret_name)
            if value:
                logger.debug(
                    f"Retrieved secret from environment",
                    metadata={"event": "secret_retrieved", "secret_name": secret_name, "source": "env"}
                )
            return value
        
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
                        logger.debug(
                            f"Retrieved secret from Dapr",
                            metadata={
                                "event": "secret_retrieved",
                                "secret_name": secret_name,
                                "source": "dapr",
                                "store": self.secret_store_name
                            }
                        )
                        return str(value)
                    
                    # If not found by key, try getting first value
                    if response.secret:
                        values = list(response.secret.values())
                        if values:
                            logger.debug(
                                f"Retrieved secret from Dapr (first value)",
                                metadata={
                                    "event": "secret_retrieved",
                                    "secret_name": secret_name,
                                    "source": "dapr",
                                    "store": self.secret_store_name
                                }
                            )
                            return str(values[0])
                
                elif response.secret:
                    # Direct value
                    logger.debug(
                        f"Retrieved secret from Dapr (direct)",
                        metadata={
                            "event": "secret_retrieved",
                            "secret_name": secret_name,
                            "source": "dapr",
                            "store": self.secret_store_name
                        }
                    )
                    return str(response.secret)
                    
                # If we get here, no value was found in Dapr
                logger.warning(
                    f"Secret not found in Dapr store",
                    metadata={
                        "event": "secret_not_found",
                        "secret_name": secret_name,
                        "store": self.secret_store_name
                    }
                )
                
        except Exception as e:
            logger.warning(
                f"Failed to get secret from Dapr: {str(e)}",
                metadata={
                    "event": "secret_retrieval_error",
                    "secret_name": secret_name,
                    "error": str(e),
                    "store": self.secret_store_name
                }
            )
        
        # Fallback to environment variable
        value = os.getenv(secret_name)
        if value:
            logger.debug(
                f"Retrieved secret from environment (fallback)",
                metadata={
                    "event": "secret_retrieved",
                    "secret_name": secret_name,
                    "source": "env_fallback"
                }
            )
        return value
    
    def get_multiple_secrets(self, secret_names: list[str]) -> Dict[str, Optional[str]]:
        """
        Get multiple secrets at once.
        
        Args:
            secret_names: List of secret names to retrieve
            
        Returns:
            Dictionary mapping secret names to their values
        """
        return {name: self.get_secret(name) for name in secret_names}


# Global instance
secret_manager = DaprSecretManager()


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from secrets or environment variables.
    
    Returns:
        Dictionary with database connection parameters
    """
    return {
        'host': secret_manager.get_secret('MONGODB_HOST') or 'localhost',
        'port': int(secret_manager.get_secret('MONGODB_PORT') or '27019'),
        'username': secret_manager.get_secret('MONGODB_USERNAME'),
        'password': secret_manager.get_secret('MONGODB_PASSWORD'),
        'database': secret_manager.get_secret('MONGODB_DATABASE') or 'productdb',
    }


def get_jwt_config() -> Dict[str, Any]:
    """
    Get JWT configuration from secrets or environment variables.
    
    Returns:
        Dictionary with JWT configuration parameters
    """
    return {
        'secret': secret_manager.get_secret('JWT_SECRET') or 'your_jwt_secret_key',
        'algorithm': secret_manager.get_secret('JWT_ALGORITHM') or 'HS256',
        'expiration': int(secret_manager.get_secret('JWT_EXPIRATION') or '3600')
    }
