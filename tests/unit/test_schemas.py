"""Unit tests for product models and schemas"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.product import Product, ProductBase
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse


class TestProductModel:
    """Test Product domain model"""

    def test_product_model_creation(self):
        """Test creating a Product model"""
        now = datetime.utcnow()
        product = Product(
            id="507f1f77bcf86cd799439011",
            name="Test Product",
            price=29.99,
            description="A great test product",
            category="Electronics",
            brand="TestBrand",
            sku="TEST-001",
            created_by="admin123"
        )
        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.sku == "TEST-001"
        assert product.id == "507f1f77bcf86cd799439011"

    def test_product_base_model(self):
        """Test ProductBase model without ID"""
        product = ProductBase(
            name="Base Product",
            price=19.99,
            sku="BASE-001",
            created_by="user123"
        )
        assert product.name == "Base Product"
        assert product.created_by == "user123"


class TestProductSchemas:
    """Test product API schemas"""

    def test_product_create_schema(self):
        """Test ProductCreate schema validation"""
        product_data = {
            "name": "Test Product",
            "price": 29.99,
            "description": "A great test product",
            "category": "Electronics",
            "brand": "TestBrand",
            "sku": "TEST-001"
        }
        product = ProductCreate(**product_data)
        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.sku == "TEST-001"

    def test_product_create_name_validation(self):
        """Test product name validation in ProductCreate"""
        # Test valid names
        valid_names = ["Product", "A", "x" * 100]  # 1 to 100 characters
        for name in valid_names:
            product = ProductCreate(name=name, price=10.0, sku="TEST-001")
            assert product.name == name

        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="", price=10.0, sku="TEST-001")
        errors = exc_info.value.errors()
        assert any("String should have at least 1 character" in str(error) for error in errors)

        # Test name too long (over 255 characters)
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="x" * 256, price=10.0, sku="TEST-001")
        errors = exc_info.value.errors()
        assert any("String should have at most 255 characters" in str(error) for error in errors)

    def test_product_create_price_validation(self):
        """Test product price validation"""
        # Test valid prices
        valid_prices = [0.0, 0.01, 1.0, 999999.99]  # Updated to include 0
        for price in valid_prices:
            product = ProductCreate(name="Test", price=price, sku="TEST-001")
            assert product.price == price

        # Test negative price
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="Test", price=-1.0, sku="TEST-001")
        errors = exc_info.value.errors()
        assert any("Input should be greater than or equal to 0" in str(error) for error in errors)

    def test_product_create_sku_validation(self):
        """Test product SKU validation"""
        # Test valid SKUs
        valid_skus = ["A", "SKU-123", "PROD_001", "x" * 50]
        for sku in valid_skus:
            product = ProductCreate(name="Test", price=10.0, sku=sku)
            assert product.sku == sku

        # Test None SKU (should be allowed)
        product = ProductCreate(name="Test", price=10.0, sku=None)
        assert product.sku is None

        # Test SKU too long (over 50 characters)
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="Test", price=10.0, sku="x" * 51)
        errors = exc_info.value.errors()
        assert any("String should have at most 50 characters" in str(error) for error in errors)

    def test_product_update_schema(self):
        """Test ProductUpdate schema allows partial updates"""
        # Test partial update with just name
        update = ProductUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.price is None
        assert update.description is None

        # Test partial update with price and description
        update = ProductUpdate(price=99.99, description="Updated description")
        assert update.price == 99.99
        assert update.description == "Updated description"
        assert update.name is None

    def test_product_response_schema(self):
        """Test ProductResponse schema"""
        response_data = {
            "id": "507f1f77bcf86cd799439011",
            "name": "Test Product", 
            "price": 29.99,
            "sku": "TEST-001",
            "created_by": "user123"
        }
        response = ProductResponse(**response_data)
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.name == "Test Product"

    def test_product_create_optional_fields(self):
        """Test ProductCreate with optional fields"""
        # Minimum required fields
        product = ProductCreate(name="Test", price=10.0)
        assert product.description is None
        assert product.category is None
        assert product.brand is None
        assert product.sku is None

        # With optional fields
        product = ProductCreate(
            name="Test",
            price=10.0,
            sku="TEST-001",
            description="Test description",
            category="Electronics",
            brand="TestBrand"
        )
        assert product.description == "Test description"
        assert product.category == "Electronics"
        assert product.brand == "TestBrand"