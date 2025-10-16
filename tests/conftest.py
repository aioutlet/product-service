"""Shared test fixtures"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from bson import ObjectId

from src.shared.models.review import Review, ReviewReport


@pytest.fixture
def mock_collection():
    """Mock MongoDB collection for testing"""
    collection = AsyncMock()
    return collection


@pytest.fixture
def sample_review():
    """Sample review for testing"""
    return Review(
        user_id="user123",
        username="testuser",
        rating=5,
        comment="Great product!"
    )


@pytest.fixture
def sample_review_report():
    """Sample review report for testing"""
    return ReviewReport(
        reported_by="reporter456",
        reason="Inappropriate content"
    )


@pytest.fixture
def mock_product_doc():
    """Mock product document from MongoDB"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Test Product",
        "price": 29.99,
        "reviews": [
            {
                "user_id": "user123",
                "username": "testuser",
                "rating": 5,
                "comment": "Great!",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None,
                "updated_by": None,
                "reports": []
            },
            {
                "user_id": "user456",
                "username": "anotheruser",
                "rating": 4,
                "comment": "Good product",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None,
                "updated_by": None,
                "reports": []
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
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