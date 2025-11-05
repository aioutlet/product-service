"""
Configuration Validator
Validates all required environment variables at application startup
Fails fast if any configuration is missing or invalid

NOTE: This module uses print() for validation messages because it runs BEFORE
logger initialization. The logger depends on validated config values.
"""

import os
import sys
from datetime import datetime
from urllib.parse import urlparse


def _log(message: str):
    """Print log message with timestamp in consistent format"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] INFO - {message}")


def is_valid_url(url: str) -> bool:
    """Validates a URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_port(port: str) -> bool:
    """Validates a port number"""
    try:
        port_num = int(port)
        return 0 < port_num <= 65535
    except (ValueError, TypeError):
        return False


def is_valid_log_level(level: str) -> bool:
    """Validates log level"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    return level.upper() in valid_levels


def is_valid_environment(env: str) -> bool:
    """Validates ENVIRONMENT"""
    valid_envs = ['development', 'production', 'test', 'staging']
    return env.lower() in valid_envs


def is_valid_boolean(value: str) -> bool:
    """Validates boolean string"""
    return value.lower() in ['true', 'false']


# Configuration validation rules
VALIDATION_RULES = {
    # Service Configuration
    'ENVIRONMENT': {
        'required': True,
        'validator': is_valid_environment,
        'error_message': 'ENVIRONMENT must be one of: development, production, test, staging',
    },
    'PORT': {
        'required': True,
        'validator': is_valid_port,
        'error_message': 'PORT must be a valid port number (1-65535)',
    },
    'SERVICE_NAME': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'SERVICE_NAME must be a non-empty string',
    },
    'SERVICE_VERSION': {
        'required': True,
        'validator': lambda v: v and len(v.split('.')) == 3,
        'error_message': 'SERVICE_VERSION must be in semantic version format (e.g., 1.0.0)',
    },
    
    # Database Configuration
    'MONGO_INITDB_ROOT_USERNAME': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MONGO_INITDB_ROOT_USERNAME must be a non-empty string',
    },
    'MONGO_INITDB_ROOT_PASSWORD': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MONGO_INITDB_ROOT_PASSWORD must be a non-empty string',
    },
    'MONGO_INITDB_DATABASE': {
        'required': True,
        'validator': lambda v: v and len(v) > 0,
        'error_message': 'MONGO_INITDB_DATABASE must be a non-empty string',
    },
    'MONGODB_HOST': {
        'required': False,
        'validator': lambda v: not v or len(v) > 0,
        'error_message': 'MONGODB_HOST must be a non-empty string if provided',
        'default': 'localhost',
    },
    'MONGODB_PORT': {
        'required': False,
        'validator': lambda v: not v or is_valid_port(v),
        'error_message': 'MONGODB_PORT must be a valid port number if provided',
        'default': '27017',
    },
    'MONGODB_AUTH_SOURCE': {
        'required': False,
        'validator': lambda v: not v or len(v) > 0,
        'error_message': 'MONGODB_AUTH_SOURCE must be a non-empty string if provided',
        'default': 'admin',
    },
    
    # Dapr Configuration
    'DAPR_HTTP_PORT': {
        'required': False,
        'validator': is_valid_port,
        'error_message': 'DAPR_HTTP_PORT must be a valid port number',
        'default': '3500',
    },
    'DAPR_GRPC_PORT': {
        'required': False,
        'validator': is_valid_port,
        'error_message': 'DAPR_GRPC_PORT must be a valid port number',
        'default': '50001',
    },
    'DAPR_PUBSUB_NAME': {
        'required': False,
        'validator': lambda v: not v or len(v) > 0,
        'error_message': 'DAPR_PUBSUB_NAME must be a non-empty string',
        'default': 'product-pubsub',
    },
    'DAPR_APP_ID': {
        'required': False,
        'validator': lambda v: not v or len(v) > 0,
        'error_message': 'DAPR_APP_ID must be a non-empty string',
        'default': 'product-service',
    },
    
    # Security Configuration
    'JWT_SECRET': {
        'required': True,
        'validator': lambda v: v and len(v) >= 32,
        'error_message': 'JWT_SECRET must be at least 32 characters long',
    },
    'JWT_ALGORITHM': {
        'required': False,
        'validator': lambda v: not v or v in ['HS256', 'HS384', 'HS512', 'RS256'],
        'error_message': 'JWT_ALGORITHM must be one of: HS256, HS384, HS512, RS256',
        'default': 'HS256',
    },
    'JWT_EXPIRE_MINUTES': {
        'required': False,
        'validator': lambda v: not v or (v.isdigit() and int(v) > 0),
        'error_message': 'JWT_EXPIRE_MINUTES must be a positive integer',
        'default': '480',
    },
    
    # CORS Configuration
    'CORS_ORIGINS': {
        'required': True,
        'validator': lambda v: v and all(
            origin.strip() == '*' or is_valid_url(origin.strip())
            for origin in v.split(',')
        ),
        'error_message': 'CORS_ORIGINS must be a comma-separated list of valid URLs or *',
    },
    
    # Logging Configuration
    'LOG_LEVEL': {
        'required': False,
        'validator': is_valid_log_level,
        'error_message': 'LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL',
        'default': 'INFO',
    },
    'LOG_FORMAT': {
        'required': False,
        'validator': lambda v: not v or v.lower() in ['json', 'console'],
        'error_message': 'LOG_FORMAT must be either json or console',
        'default': 'json',
    },
    'LOG_TO_CONSOLE': {
        'required': False,
        'validator': is_valid_boolean,
        'error_message': 'LOG_TO_CONSOLE must be true or false',
        'default': 'true',
    },
    'LOG_TO_FILE': {
        'required': False,
        'validator': is_valid_boolean,
        'error_message': 'LOG_TO_FILE must be true or false',
        'default': 'false',
    },
    
    # Observability Configuration
    # Note: Distributed tracing is handled automatically by Dapr sidecar
    'CORRELATION_ID_HEADER': {
        'required': False,
        'validator': lambda v: not v or (len(v) > 0 and all(c.islower() or c == '-' for c in v)),
        'error_message': 'CORRELATION_ID_HEADER must be lowercase with hyphens only',
        'default': 'x-correlation-id',
    },
}


def validate_config():
    """
    Validates all environment variables according to the rules
    Raises SystemExit if any required variable is missing or invalid
    """
    errors = []
    warnings = []

    _log('[CONFIG] Validating environment configuration...')

    # Validate each rule
    for key, rule in VALIDATION_RULES.items():
        value = os.getenv(key)

        # Check if required variable is missing
        if rule['required'] and not value:
            errors.append(f"❌ {key} is required but not set")
            continue

        # Skip validation if value is not set and not required
        if not value and not rule['required']:
            if 'default' in rule:
                warnings.append(f"⚠️  {key} not set, using default: {rule['default']}")
                os.environ[key] = rule['default']
            continue

        # Validate the value
        if value and rule['validator'] and not rule['validator'](value):
            errors.append(f"❌ {key}: {rule['error_message']}")
            if len(value) > 100:
                errors.append(f"   Current value: {value[:100]}...")
            else:
                errors.append(f"   Current value: {value}")

    # Log warnings
    if warnings:
        for warning in warnings:
            _log(warning)

    # If there are errors, log them and exit
    if errors:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{timestamp}] ERROR - [CONFIG] Configuration validation failed:', file=sys.stderr)
        for error in errors:
            print(f'[{timestamp}] ERROR - {error}', file=sys.stderr)
        print(f'[{timestamp}] ERROR - 💡 Please check your .env file and ensure all required variables are set correctly.', 
              file=sys.stderr)
        sys.exit(1)

    _log('[CONFIG] ✅ All required environment variables are valid')


def get_config(key: str, default=None):
    """Gets a validated configuration value"""
    return os.getenv(key, default)


def get_config_boolean(key: str, default: bool = False) -> bool:
    """Gets a validated configuration value as boolean"""
    value = os.getenv(key, str(default))
    return value.lower() == 'true'


def get_config_int(key: str, default: int = 0) -> int:
    """Gets a validated configuration value as integer"""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_config_list(key: str, default=None) -> list:
    """Gets a validated configuration value as list (comma-separated)"""
    if default is None:
        default = []
    value = os.getenv(key)
    if not value:
        return default
    return [item.strip() for item in value.split(',')]
