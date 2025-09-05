"""Tests for product validators"""
import pytest
from pydantic import ValidationError

from src.models.product_base import ProductBase


class TestProductValidators:
    """Test product validation logic"""

    def test_valid_product_creation(self):
        """Test creating a valid product"""
        product_data = {
            "name": "Test Product",
            "price": 29.99,
            "description": "A great test product",
            "category": "Electronics",
            "brand": "TestBrand",
            "sku": "TEST-001",
            "created_by": "admin123"
        }
        product = ProductBase(**product_data)
        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.description == "A great test product"
        assert product.category == "Electronics"
        assert product.brand == "TestBrand"
        assert product.sku == "TEST-001"
        assert product.created_by == "admin123"

    def test_name_validation(self):
        """Test product name validation"""
        # Test valid names
        valid_names = ["Product", "A", "x" * 100]  # 1 to 100 characters
        for name in valid_names:
            product = ProductBase(name=name, price=10.0, created_by="admin123")
            assert product.name == name

        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="", price=10.0, created_by="admin123")
        assert "Product name cannot be empty" in str(exc_info.value)

        # Test whitespace-only name
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="   ", price=10.0, created_by="admin123")
        assert "Product name cannot be empty" in str(exc_info.value)

        # Test name too long (over 100 characters)
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="x" * 101, price=10.0, created_by="admin123")
        assert "Product name must be between 1 and 100 characters" in str(exc_info.value)

    def test_price_validation(self):
        """Test price validation (must be greater than 0)"""
        # Test valid prices
        valid_prices = [0.01, 1.0, 99.99, 1000.00]
        for price in valid_prices:
            product = ProductBase(name="Test", price=price, created_by="admin123")
            assert product.price == price

        # Test invalid prices
        invalid_prices = [0, -0.01, -1.0, -100.0]
        for price in invalid_prices:
            with pytest.raises(ValidationError) as exc_info:
                ProductBase(name="Test", price=price, created_by="admin123")
            assert "Price must be greater than 0" in str(exc_info.value)

    def test_category_validation(self):
        """Test category validation (max 100 characters)"""
        # Test valid categories
        product = ProductBase(name="Test", price=10.0, category="Electronics", created_by="admin123")
        assert product.category == "Electronics"

        # Test None category (should be allowed)
        product = ProductBase(name="Test", price=10.0, category=None, created_by="admin123")
        assert product.category is None

        # Test category at limit
        max_category = "x" * 100
        product = ProductBase(name="Test", price=10.0, category=max_category, created_by="admin123")
        assert product.category == max_category

        # Test category too long
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="Test", price=10.0, category="x" * 101, created_by="admin123")
        assert "Category name must be up to 100 characters" in str(exc_info.value)

    def test_brand_validation(self):
        """Test brand validation (max 100 characters)"""
        # Test valid brand
        product = ProductBase(name="Test", price=10.0, brand="TestBrand", created_by="admin123")
        assert product.brand == "TestBrand"

        # Test None brand (should be allowed)
        product = ProductBase(name="Test", price=10.0, brand=None, created_by="admin123")
        assert product.brand is None

        # Test brand at limit
        max_brand = "x" * 100
        product = ProductBase(name="Test", price=10.0, brand=max_brand, created_by="admin123")
        assert product.brand == max_brand

        # Test brand too long
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="Test", price=10.0, brand="x" * 101, created_by="admin123")
        assert "Brand name must be up to 100 characters" in str(exc_info.value)

    def test_sku_validation(self):
        """Test SKU validation (max 100 characters)"""
        # Test valid SKU
        product = ProductBase(name="Test", price=10.0, sku="TEST-001", created_by="admin123")
        assert product.sku == "TEST-001"

        # Test None SKU (should be allowed)
        product = ProductBase(name="Test", price=10.0, sku=None, created_by="admin123")
        assert product.sku is None

        # Test SKU at limit
        max_sku = "x" * 100
        product = ProductBase(name="Test", price=10.0, sku=max_sku, created_by="admin123")
        assert product.sku == max_sku

        # Test SKU too long
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="Test", price=10.0, sku="x" * 101, created_by="admin123")
        assert "SKU must be up to 100 characters" in str(exc_info.value)

    def test_description_validation(self):
        """Test description validation (max 5000 characters)"""
        # Test valid description
        product = ProductBase(name="Test", price=10.0, description="A great product", created_by="admin123")
        assert product.description == "A great product"

        # Test None description (should be allowed)
        product = ProductBase(name="Test", price=10.0, description=None, created_by="admin123")
        assert product.description is None

        # Test description at limit
        max_description = "x" * 5000
        product = ProductBase(name="Test", price=10.0, description=max_description, created_by="admin123")
        assert product.description == max_description

        # Test description too long
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(name="Test", price=10.0, description="x" * 5001, created_by="admin123")
        assert "Description can be up to 5000 characters" in str(exc_info.value)

    def test_default_values(self):
        """Test that product has proper default values"""
        product = ProductBase(name="Test", price=10.0, created_by="admin123")
        assert product.images == []
        assert product.tags == []
        assert product.attributes == {}
        assert product.variants == []
        assert product.average_rating == 0
        assert product.num_reviews == 0
        assert product.reviews == []
        assert product.is_active is True
        assert product.history == []