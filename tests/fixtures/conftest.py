"""Shared test fixtures"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, UTC
from bson import ObjectId


@pytest.fixture
def mock_collection():
    """Mock MongoDB collection for testing"""
    collection = AsyncMock()
    return collection


@pytest.fixture
def mock_product_doc():
    """Mock product document from MongoDB"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Test Product",
        "price": 29.99,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }


@pytest.fixture
def acting_user():
    """Sample acting user for testing"""
    return {
        "user_id": "user123",
        "username": "testuser",
        "roles": ["user"]
    }


@pytest.fixture
def admin_user():
    """Sample admin user for testing"""
    return {
        "user_id": "admin123",
        "username": "admin",
        "roles": ["admin", "user"]
    }


@pytest.fixture
def product_id():
    """Sample product ID for testing"""
    return "507f1f77bcf86cd799439011"
