"""Unit tests for product services (business logic)"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.product import ProductService
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.core.errors import ErrorResponse


class TestProductService:
    """Test ProductService business logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_repository = AsyncMock()
        self.service = ProductService(repository=self.mock_repository)

    @pytest.mark.asyncio
    async def test_create_product_success(self):
        """Test successful product creation"""
        # Arrange
        product_data = ProductCreate(
            name="Test Product",
            price=29.99,
            sku="TEST-001",
            category="Electronics"
        )
        
        created_product = ProductResponse(
            id="507f1f77bcf86cd799439011",
            name="Test Product",
            price=29.99,
            sku="TEST-001",
            category="Electronics",
            created_by="user123"
        )
        
        self.mock_repository.check_sku_exists.return_value = False  # No duplicate SKU
        self.mock_repository.create.return_value = created_product

        # Act
        result = await self.service.create_product(product_data, created_by="user123")

        # Assert
        assert result == created_product
        self.mock_repository.check_sku_exists.assert_called_once_with("TEST-001")
        self.mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self):
        """Test product creation with duplicate SKU"""
        # Arrange
        product_data = ProductCreate(
            name="Test Product",
            price=29.99,
            sku="TEST-001"
        )
        
        self.mock_repository.check_sku_exists.return_value = True

        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await self.service.create_product(product_data, created_by="user123")
        
        assert "A product with this SKU already exists" in exc_info.value.message
        assert exc_info.value.status_code == 400
        self.mock_repository.check_sku_exists.assert_called_once_with("TEST-001")
        self.mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_product_success(self):
        """Test successful product update"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        update_data = ProductUpdate(name="Updated Product", price=39.99)
        
        updated_product = ProductResponse(
            id=product_id,
            name="Updated Product",
            price=39.99,
            sku="TEST-001",
            created_by="user123"
        )
        
        self.mock_repository.update.return_value = updated_product

        # Act
        result = await self.service.update_product(product_id, update_data, updated_by="admin")

        # Assert
        assert result == updated_product
        self.mock_repository.update.assert_called_once_with(product_id, update_data, "admin")

    @pytest.mark.asyncio
    async def test_update_product_not_found(self):
        """Test updating non-existent product"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        update_data = ProductUpdate(name="Updated Product")
        
        self.mock_repository.update.return_value = None

        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await self.service.update_product(product_id, update_data, updated_by="admin")
        
        assert "Product not found" in exc_info.value.message
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_product_success(self):
        """Test successful product deletion"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        self.mock_repository.delete.return_value = True

        # Act
        result = await self.service.delete_product(product_id)

        # Assert
        assert result is None  # delete_product returns None
        self.mock_repository.delete.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self):
        """Test deleting non-existent product"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        self.mock_repository.delete.return_value = False

        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await self.service.delete_product(product_id)
        
        assert "Product not found" in exc_info.value.message
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_product_success(self):
        """Test getting a product by ID"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        product = ProductResponse(
            id=product_id,
            name="Test Product",
            price=29.99,
            sku="TEST-001",
            created_by="user123"
        )
        
        self.mock_repository.get_by_id.return_value = product

        # Act
        result = await self.service.get_product(product_id)

        # Assert
        assert result == product
        self.mock_repository.get_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_not_found(self):
        """Test getting non-existent product"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        self.mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await self.service.get_product(product_id)
        
        assert "Product not found" in exc_info.value.message
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_search_products(self):
        """Test searching products"""
        # Arrange
        search_text = "electronics"
        
        # Mock repository to return tuple
        products = [
            ProductResponse(id="1", name="Product 1", price=10.0, sku="SKU-1", created_by="user1"),
            ProductResponse(id="2", name="Product 2", price=20.0, sku="SKU-2", created_by="user2")
        ]
        total_count = 2
        
        self.mock_repository.search.return_value = (products, total_count)

        # Act
        result = await self.service.search_products(
            search_text=search_text,
            category="Electronics",
            min_price=10.0,
            max_price=100.0
        )

        # Assert
        assert result.products == products
        assert result.total_count == 2
        self.mock_repository.search.assert_called_once_with(
            search_text, None, "Electronics", None, 10.0, 100.0, None, 0, 20
        )

    @pytest.mark.asyncio
    async def test_list_products(self):
        """Test listing products with pagination"""
        # Arrange
        products = [
            ProductResponse(id="1", name="Product 1", price=10.0, sku="SKU-1", created_by="user1"),
            ProductResponse(id="2", name="Product 2", price=20.0, sku="SKU-2", created_by="user2")
        ]
        total_count = 2
        
        self.mock_repository.list_products.return_value = (products, total_count)

        # Act
        result = await self.service.list_products(skip=0, limit=10)

        # Assert
        assert result.products == products
        assert result.total_count == 2
        self.mock_repository.list_products.assert_called_once_with(
            None, None, None, None, None, None, 0, 10
        )