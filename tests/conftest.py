"""Shared test fixtures for unit, integration, and e2e tests"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, UTC
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient


# Mock database connection before importing main
@pytest.fixture(scope="session", autouse=True)
def mock_db_connection():
    """Mock MongoDB connection for all tests"""
    with patch('app.db.mongodb.connect_to_mongo', new_callable=AsyncMock) as mock_connect, \
         patch('app.db.mongodb.close_mongo_connection', new_callable=AsyncMock) as mock_close:
        mock_connect.return_value = None
        mock_close.return_value = None
        yield


# Import after mocking
from main import app
from app.models.product import Product
from app.schemas.product import ProductCreate


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture
def mock_collection():
    """Mock MongoDB collection for unit testing"""
    collection = AsyncMock()
    return collection


@pytest.fixture
async def test_db():
    """Test database for integration tests"""
    # In a real setup, this would connect to a test database
    # client = AsyncIOMotorClient("mongodb://localhost:27017")
    # db = client.test_product_service
    # yield db
    # await client.drop_database("test_product_service")
    # client.close()
    
    # For now, return None as placeholder
    yield None


# Product fixtures
@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "name": "Test Product",
        "price": 29.99,
        "description": "A great test product",
        "category": "Electronics",
        "brand": "TestBrand",
        "sku": "TEST-001"
    }


@pytest.fixture
def sample_product_create():
    """Sample ProductCreate schema for testing"""
    return ProductCreate(
        name="Test Product",
        price=29.99,
        description="A great test product",
        category="Electronics",
        brand="TestBrand",
        sku="TEST-001"
    )


@pytest.fixture
def sample_product_model():
    """Sample Product model for testing"""
    return Product(
        id="507f1f77bcf86cd799439011",
        name="Test Product",
        price=29.99,
        description="A great test product",
        category="Electronics",
        brand="TestBrand",
        sku="TEST-001",
        created_by="user123"
    )


@pytest.fixture
def mock_product_doc():
    """Mock product document from MongoDB"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Test Product",
        "price": 29.99,
        "description": "A great test product",
        "category": "Electronics",
        "brand": "TestBrand",
        "sku": "TEST-001",
        "in_stock": True,
        "created_by": "user123",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }


# User fixtures
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


# ID fixtures
@pytest.fixture
def product_id():
    """Sample product ID for testing"""
    return "507f1f77bcf86cd799439011"


@pytest.fixture
def invalid_product_id():
    """Invalid product ID for testing error cases"""
    return "invalid_id_format"


# API client fixtures
@pytest.fixture
def test_client():
    """Test client for e2e testing"""
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Async test client for e2e testing"""
    # This would be used for async e2e tests
    # from httpx import AsyncClient
    # async with AsyncClient(app=app, base_url="http://test") as client:
    #     yield client
    yield None