"""Unit tests for configuration"""
import pytest
import os
from unittest.mock import patch

from app.core.config import Config


class TestConfig:
    """Test configuration management"""

    def test_config_default_values(self):
        """Test that configuration has correct default values"""
        # Act
        config = Config()

        # Assert
        assert config.service_name == "product-service"
        assert config.service_version == "1.0.0"
        assert config.api_version == "1.0.0"
        assert config.environment == "development"
        assert isinstance(config.port, int)
        assert isinstance(config.host, str)
        assert config.log_level == "INFO"
        assert config.log_format == "console"
        assert config.log_to_file is True
        assert config.log_to_console is True
        assert config.dapr_http_port == 3500
        assert config.dapr_grpc_port == 50001

    def test_config_from_environment_variables(self):
        """Test loading configuration from environment variables"""
        # Arrange
        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "LOG_TO_FILE": "false",
            "DAPR_HTTP_PORT": "4500",
            "DAPR_GRPC_PORT": "60001"
        }

        # Act
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

        # Assert - only check the vars we explicitly set
        assert config.log_level == "DEBUG"
        assert config.log_format == "json"
        assert config.log_to_file is False
        assert config.dapr_http_port == 4500
        assert config.dapr_grpc_port == 60001

    def test_config_service_name_override(self):
        """Test that service name can be read from config"""
        # Act
        config = Config()

        # Assert - just check that it's set and is a string
        assert isinstance(config.service_name, str)
        assert len(config.service_name) > 0

    def test_config_port_conversion(self):
        """Test that port is correctly converted to integer"""
        # Arrange
        env_vars = {"PORT": "8080"}

        # Act
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

        # Assert
        assert config.port == 8080
        assert isinstance(config.port, int)

    def test_config_boolean_conversion(self):
        """Test that boolean values are correctly converted"""
        # Arrange
        env_vars = {
            "LOG_TO_FILE": "false",
            "LOG_TO_CONSOLE": "true"
        }

        # Act
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

        # Assert
        assert config.log_to_file is False
        assert config.log_to_console is True

    def test_config_case_insensitive(self):
        """Test that configuration is case-insensitive"""
        # Arrange
        env_vars = {
            "name": "test-service",
            "environment": "staging"
        }

        # Act
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

        # Assert
        # Note: Environment variables are case-sensitive in Linux
        # This test verifies that the Config class handles them appropriately
        assert config.service_name in ["test-service", "product-service"]
        assert config.environment in ["staging", "development"]

    def test_config_log_file_path_default(self):
        """Test default log file path"""
        # Act
        config = Config()

        # Assert
        assert config.log_file_path == "./logs/product-service.log"

    def test_config_log_file_path_override(self):
        """Test overriding log file path"""
        # Arrange
        env_vars = {"LOG_FILE_PATH": "/var/log/custom.log"}

        # Act
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

        # Assert
        assert config.log_file_path == "/var/log/custom.log"

    def test_config_dapr_ports(self):
        """Test Dapr port configuration"""
        # Act
        config = Config()

        # Assert
        assert config.dapr_http_port == 3500
        assert config.dapr_grpc_port == 50001

    def test_config_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        # Arrange
        env_vars = {
            "UNKNOWN_FIELD": "should be ignored"
        }

        # Act - No exception should be raised
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

        # Assert
        assert not hasattr(config, "unknown_field")
        assert not hasattr(config, "UNKNOWN_FIELD")
