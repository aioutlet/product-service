"""Additional unit tests for product models and edge cases"""
import pytest
from datetime import datetime, UTC
from pydantic import ValidationError

from app.models.product import Product, ProductBase, RatingDistribution
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse


class TestProductModelEdgeCases:
    """Test Product model edge cases"""

    def test_product_with_minimum_fields(self):
        """Test creating a Product with only required fields"""
        product = Product(
            id="507f1f77bcf86cd799439011",
            name="Minimal Product",
            price=0.0,
            created_by="user123"
        )
        assert product.name == "Minimal Product"
        assert product.price == 0.0
        assert product.sku is None
        assert product.description is None

    def test_product_with_all_fields(self):
        """Test creating a Product with all fields populated"""
        now = datetime.now(UTC)
        product = Product(
            id="507f1f77bcf86cd799439011",
            name="Complete Product",
            price=99.99,
            description="Complete description",
            category="Electronics",
            brand="TestBrand",
            sku="COMPLETE-001",
            department="Technology",
            subcategory="Gadgets",
            tags=["tag1", "tag2"],
            is_active=True,
            created_by="user123",
            updated_by="admin123",
            created_at=now,
            updated_at=now
        )
        assert product.name == "Complete Product"
        assert product.tags == ["tag1", "tag2"]
        assert product.department == "Technology"

    def test_rating_distribution_model(self):
        """Test RatingDistribution nested model"""
        rating_dist = RatingDistribution(
            one_star=5,
            two_star=10,
            three_star=20,
            four_star=30,
            five_star=35
        )
        assert rating_dist.one_star == 5
        assert rating_dist.five_star == 35

    def test_product_with_rating_info(self):
        """Test Product with rating information"""
        from app.models.product import ReviewAggregates
        
        rating_dist = RatingDistribution(
            one_star=2,
            two_star=3,
            three_star=10,
            four_star=25,
            five_star=60
        )
        
        review_aggs = ReviewAggregates(
            average_rating=4.5,
            total_review_count=100,
            verified_review_count=80,
            rating_distribution=rating_dist
        )
        
        product = Product(
            id="507f1f77bcf86cd799439011",
            name="Rated Product",
            price=49.99,
            created_by="user123",
            review_aggregates=review_aggs
        )
        assert product.review_aggregates.average_rating == 4.5
        assert product.review_aggregates.total_review_count == 100
        assert product.review_aggregates.rating_distribution.five_star == 60


class TestProductSchemaEdgeCases:
    """Test product schema edge cases"""

    def test_product_create_with_long_description(self):
        """Test ProductCreate with maximum description length"""
        long_description = "A" * 1000  # Long but valid description
        product = ProductCreate(
            name="Test Product",
            price=29.99,
            description=long_description,
            sku="TEST-001"
        )
        assert product.description == long_description

    def test_product_create_zero_price(self):
        """Test ProductCreate with zero price (valid case)"""
        product = ProductCreate(
            name="Free Product",
            price=0.0,
            sku="FREE-001"
        )
        assert product.price == 0.0

    def test_product_create_with_tags(self):
        """Test ProductCreate with tags"""
        tags = ["electronics", "sale", "new"]
        product = ProductCreate(
            name="Tagged Product",
            price=29.99,
            tags=tags,
            sku="TAG-001"
        )
        assert product.tags == tags

    def test_product_update_partial_fields(self):
        """Test ProductUpdate with various partial updates"""
        # Update only name
        update1 = ProductUpdate(name="New Name")
        assert update1.name == "New Name"
        assert update1.price is None
        
        # Update only price
        update2 = ProductUpdate(price=99.99)
        assert update2.price == 99.99
        assert update2.name is None
        
        # Update multiple fields
        update3 = ProductUpdate(name="Updated", price=149.99, description="New desc")
        assert update3.name == "Updated"
        assert update3.price == 149.99
        assert update3.description == "New desc"

    def test_product_update_empty(self):
        """Test ProductUpdate with no fields"""
        update = ProductUpdate()
        assert update.name is None
        assert update.price is None
        assert update.description is None

    def test_product_response_with_all_fields(self):
        """Test ProductResponse with complete data"""
        from app.models.product import ReviewAggregates
        
        now = datetime.now(UTC)
        review_aggs = ReviewAggregates(
            average_rating=4.2,
            total_review_count=42,
            verified_review_count=30
        )
        
        response = ProductResponse(
            id="507f1f77bcf86cd799439011",
            name="Response Product",
            price=79.99,
            description="Full response",
            category="Electronics",
            brand="TestBrand",
            sku="RESP-001",
            department="Tech",
            subcategory="Gadgets",
            tags=["new", "featured"],
            is_active=True,
            review_aggregates=review_aggs,
            created_by="user123",
            updated_by="admin123",
            created_at=now,
            updated_at=now
        )
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.review_aggregates.average_rating == 4.2
        assert response.department == "Tech"


class TestProductValidationErrors:
    """Test validation error scenarios"""

    def test_product_create_invalid_name(self):
        """Test ProductCreate with invalid name"""
        # Empty string
        with pytest.raises(ValidationError):
            ProductCreate(name="", price=10.0, sku="TEST-001")
        
        # Too long (over 255 characters)
        with pytest.raises(ValidationError):
            ProductCreate(name="x" * 256, price=10.0, sku="TEST-001")

    def test_product_create_negative_price(self):
        """Test ProductCreate with negative price"""
        with pytest.raises(ValidationError):
            ProductCreate(name="Test", price=-10.0, sku="TEST-001")

    def test_product_create_invalid_sku(self):
        """Test ProductCreate with invalid SKU"""
        # Too long (over 50 characters)
        with pytest.raises(ValidationError):
            ProductCreate(name="Test", price=10.0, sku="x" * 51)

    def test_product_missing_required_fields(self):
        """Test Product creation with missing required fields"""
        # Missing name
        with pytest.raises(ValidationError):
            ProductCreate(price=10.0, sku="TEST-001")
        
        # Missing price
        with pytest.raises(ValidationError):
            ProductCreate(name="Test", sku="TEST-001")
