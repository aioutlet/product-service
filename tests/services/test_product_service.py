"""Unit tests for ProductService"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
from bson import ObjectId

# Import directly to avoid circular import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.repositories.product_repository import ProductRepository
from src.models.product import ProductCreate, ProductUpdate, ProductDB, ProductImage
from src.core.errors import ErrorResponse


class TestProductService:
    """Test cases for ProductService class"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock ProductRepository"""
        repo = AsyncMock(spec=ProductRepository)
        repo.collection = AsyncMock()
        repo._to_object_id = lambda x: ObjectId(x) if ObjectId.is_valid(x) else None
        return repo
    
    @pytest.fixture
    def product_service(self, mock_repository):
        """Create ProductService instance with mocked repository"""
        from src.services.product_service import ProductService
        return ProductService(mock_repository)
    
    @pytest.fixture
    def sample_product_doc(self):
        """Sample product document"""
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "name": "Test Product",
            "description": "Test Description",
            "price": 29.99,
            "category": "Electronics",
            "brand": "TestBrand",
            "sku": "TEST-001",
            "tags": ["test", "electronics"],
            "images": [{"url": "image1.jpg", "alt": "Test Image", "is_primary": True, "order": 1}],
            "attributes": {"color": "blue"},
            "is_active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "created_by": "user123"
        }
    
    @pytest.fixture
    def sample_product_create(self):
        """Sample ProductCreate data"""
        from src.models.product import ProductImage
        return ProductCreate(
            name="New Product",
            description="New Description",
            price=39.99,
            category="Electronics",
            brand="TestBrand",
            sku="NEW-001",
            tags=["new", "test"],
            images=[ProductImage(url="new-image.jpg", alt="New Image")],
            attributes={"color": "red"},
            created_by="test-user"
        )
    
    @pytest.fixture
    def admin_user(self):
        """Mock admin user"""
        user = MagicMock()
        user.user_id = "admin123"
        user.username = "admin"
        user.has_role = MagicMock(return_value=True)
        return user
    
    @pytest.fixture
    def regular_user(self):
        """Mock regular user"""
        user = MagicMock()
        user.user_id = "user123"
        user.username = "testuser"
        user.has_role = MagicMock(return_value=False)
        return user


class TestGetProductById(TestProductService):
    """Tests for get_product_by_id method"""
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_success(
        self, product_service, mock_repository, sample_product_doc
    ):
        """Test successful product retrieval by ID"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_repository.find_by_id.return_value = sample_product_doc
        
        # Act
        result = await product_service.get_product_by_id(product_id)
        
        # Assert
        assert result == sample_product_doc
        mock_repository.find_by_id.assert_called_once_with(product_id, None)
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(
        self, product_service, mock_repository
    ):
        """Test product not found"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_repository.find_by_id.return_value = None
        
        # Act
        result = await product_service.get_product_by_id(product_id)
        
        # Assert
        assert result is None
        mock_repository.find_by_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_invalid_id(
        self, product_service, mock_repository
    ):
        """Test with invalid ObjectId"""
        # Arrange
        invalid_id = "invalid-id"
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.get_product_by_id(invalid_id)
        
        assert exc_info.value.status_code == 400
        assert "Invalid product ID format" in exc_info.value.message


class TestCreateProduct(TestProductService):
    """Tests for create_product method"""
    
    @pytest.mark.asyncio
    async def test_create_product_success(
        self, product_service, mock_repository, sample_product_create, 
        sample_product_doc
    ):
        """Test successful product creation"""
        # Arrange
        mock_repository.is_sku_unique.return_value = True
        product_id = "507f1f77bcf86cd799439011"
        mock_repository.create.return_value = product_id
        mock_repository.find_by_id.return_value = sample_product_doc
        
        # Mock Dapr publisher
        with patch('src.services.dapr_publisher.get_dapr_publisher') as mock_get_dapr:
            mock_publisher = AsyncMock()
            mock_get_dapr.return_value = mock_publisher
            
            # Act
            result = await product_service.create_product(
                sample_product_create,
                "correlation-123"
            )
            
            # Assert
            assert result == product_id
            mock_repository.is_sku_unique.assert_called_once_with("NEW-001", correlation_id="correlation-123")
            mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(
        self, product_service, mock_repository, sample_product_create,
        sample_product_doc
    ):
        """Test creating product with duplicate SKU"""
        # Arrange
        mock_repository.is_sku_unique.return_value = False
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.create_product(
                sample_product_create
            )
        
        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_create_product_negative_price(
        self, product_service, admin_user
    ):
        """Test creating product with negative price (should be caught by Pydantic)"""
        # Arrange - Pydantic will validate before reaching the service
        # This test verifies Pydantic validation works
        from pydantic import ValidationError
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            invalid_product = ProductCreate(
                name="Invalid Product",
                price=-10.0,
                category="Test",
                brand="Test",
                sku="INVALID-001",
                created_by="test-user"
            )
        
        # Verify it's a price validation error
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('price',) for error in errors)


class TestUpdateProduct(TestProductService):
    """Tests for update_product method"""
    
    @pytest.mark.asyncio
    async def test_update_product_success(
        self, product_service, mock_repository, sample_product_doc, admin_user
    ):
        """Test successful product update"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        updates = {"name": "Updated Product", "price": 49.99}
        
        updated_doc = {**sample_product_doc, **updates}
        mock_repository.collection.find_one.return_value = updated_doc
        mock_repository.collection.update_one.return_value = MagicMock(modified_count=1)
        
        # Mock Dapr publisher
        with patch('src.services.dapr_publisher.get_dapr_publisher') as mock_get_dapr:
            mock_publisher = AsyncMock()
            mock_get_dapr.return_value = mock_publisher
            
            # Act
            result = await product_service.update_product(
                product_id,
                updates,
                mock_repository.collection,
                admin_user,
                "correlation-123"
            )
            
            # Assert
            assert result is not None
            mock_repository.collection.find_one.assert_called()
            mock_repository.collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_product_not_found(
        self, product_service, mock_repository, admin_user
    ):
        """Test updating non-existent product"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        updates = {"name": "Updated Product"}
        mock_repository.collection.find_one.return_value = None
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.update_product(
                product_id, 
                updates, 
                mock_repository.collection,
                admin_user
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_update_product_not_admin(
        self, product_service, mock_repository, sample_product_doc, regular_user
    ):
        """Test updating product without admin role"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        updates = {"name": "Updated Product"}
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.update_product(
                product_id, 
                updates, 
                mock_repository.collection,
                regular_user
            )
        
        assert exc_info.value.status_code == 403


class TestDeleteProduct(TestProductService):
    """Tests for delete_product method"""
    
    @pytest.mark.asyncio
    async def test_delete_product_success(
        self, product_service, mock_repository, sample_product_doc, admin_user
    ):
        """Test successful product deletion (soft delete)"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_repository.collection.find_one.return_value = sample_product_doc
        mock_repository.collection.update_one.return_value = MagicMock(
            modified_count=1
        )
        
        # Mock Dapr publisher
        with patch('src.services.dapr_publisher.get_dapr_publisher') as mock_get_dapr:
            mock_publisher = AsyncMock()
            mock_get_dapr.return_value = mock_publisher
            
            # Act
            result = await product_service.delete_product(
                product_id,
                mock_repository.collection,
                admin_user,
                "correlation-123"
            )
            
            # Assert - delete_product returns None
            assert result is None
            mock_repository.collection.update_one.assert_called_once()
            
            # Verify soft delete fields were set
            call_args = mock_repository.collection.update_one.call_args
            update_data = call_args[0][1]["$set"]
            assert update_data["is_active"] is False
            assert "updated_at" in update_data
    
    @pytest.mark.asyncio
    async def test_delete_product_not_found(
        self, product_service, mock_repository, admin_user
    ):
        """Test deleting non-existent product"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_repository.collection.find_one.return_value = None
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.delete_product(
                product_id, 
                mock_repository.collection,
                admin_user
            )
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_product_not_admin(
        self, product_service, mock_repository, sample_product_doc, regular_user
    ):
        """Test deleting product without admin role"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.delete_product(
                product_id, 
                mock_repository.collection,
                regular_user
            )
        
        assert exc_info.value.status_code == 403


class TestSearchProducts(TestProductService):
    """Tests for search_products method"""
    
    @pytest.mark.asyncio
    async def test_search_products_success(
        self, product_service, mock_repository, sample_product_doc
    ):
        """Test successful product search"""
        # Arrange
        mock_repository.search_products.return_value = ([sample_product_doc], 1)
        
        # Act
        products, total = await product_service.search_products(
            search_text="test",
            skip=0,
            limit=10
        )
        
        # Assert
        assert len(products) == 1
        assert total == 1
        mock_repository.search_products.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_products_with_filters(
        self, product_service, mock_repository, sample_product_doc
    ):
        """Test product search with filters"""
        # Arrange
        mock_repository.search_products.return_value = ([sample_product_doc], 1)
        
        # Act
        products, total = await product_service.search_products(
            search_text="test",
            category="Electronics",
            min_price=20.0,
            max_price=50.0,
            tags=["test"],
            skip=0,
            limit=10
        )
        
        # Assert
        assert len(products) == 1
        mock_repository.search_products.assert_called_once()
        
        # Verify filters were passed
        call_kwargs = mock_repository.search_products.call_args[1]
        assert call_kwargs["category"] == "Electronics"
        assert call_kwargs["min_price"] == 20.0


class TestGetActiveProducts(TestProductService):
    """Tests for get_active_products method"""
    
    @pytest.mark.asyncio
    async def test_get_active_products_success(
        self, product_service, mock_repository, sample_product_doc
    ):
        """Test retrieving active products"""
        # Arrange
        mock_repository.get_active_products.return_value = ([sample_product_doc], 1)
        
        # Act
        products, total = await product_service.get_active_products(
            skip=0,
            limit=10
        )
        
        # Assert
        assert len(products) == 1
        assert total == 1
        mock_repository.get_active_products.assert_called_once()


class TestReactivateProduct(TestProductService):
    """Tests for reactivate_product method"""
    
    @pytest.mark.asyncio
    async def test_reactivate_product_success(
        self, product_service, mock_repository, sample_product_doc, admin_user
    ):
        """Test successful product reactivation"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        deleted_doc = {**sample_product_doc, "is_active": False}
        reactivated_doc = {**sample_product_doc, "is_active": True}
        
        # Mock find_one to return: 1) deleted product, 2) None for SKU check, 3) reactivated product
        mock_repository.collection.find_one.side_effect = [deleted_doc, None, reactivated_doc]
        mock_repository.collection.update_one.return_value = MagicMock(modified_count=1)
        
        # Act
        result = await product_service.reactivate_product(
            product_id,
            mock_repository.collection,
            admin_user,
            "correlation-123"
        )
        
        # Assert
        assert result is not None
        assert result.is_active is True
        assert mock_repository.collection.find_one.call_count == 3  # Product, SKU check, final result
    
    @pytest.mark.asyncio
    async def test_reactivate_product_already_active(
        self, product_service, mock_repository, sample_product_doc, admin_user
    ):
        """Test reactivating already active product"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_repository.collection.find_one.return_value = sample_product_doc
        
        # Act & Assert
        with pytest.raises(ErrorResponse) as exc_info:
            await product_service.reactivate_product(
                product_id, 
                mock_repository.collection,
                admin_user
            )
        
        assert exc_info.value.status_code == 400
        assert "already active" in exc_info.value.message.lower()


class TestGetTrendingProducts(TestProductService):
    """Tests for get_trending_products method"""
    
    @pytest.mark.asyncio
    async def test_get_trending_products_success(
        self, product_service, mock_repository, sample_product_doc
    ):
        """Test retrieving trending products"""
        # Arrange - Create mock cursor that returns synchronously  
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__.return_value = iter([sample_product_doc])
        
        # find() should return cursor immediately (not async)
        mock_repository.collection.find = MagicMock(return_value=mock_cursor)
        
        # Act
        result = await product_service.get_trending_products(
            mock_repository.collection,
            limit=5
        )
        
        # Assert
        assert len(result) == 1
        mock_repository.collection.find.assert_called_once()


class TestGetAdminStats(TestProductService):
    """Tests for get_admin_stats method"""
    
    @pytest.mark.asyncio
    async def test_get_admin_stats_success(
        self, product_service, mock_repository
    ):
        """Test retrieving admin statistics"""
        # Arrange
        mock_repository.collection.count_documents = AsyncMock(
            side_effect=[100, 80]  # total, active
        )
        
        # Act
        result = await product_service.get_admin_stats(mock_repository.collection)
        
        # Assert
        assert result["total"] == 100
        assert result["active"] == 80
        assert result["lowStock"] == 0
        assert result["outOfStock"] == 0


class TestListProducts(TestProductService):
    """Tests for list_products method"""
    
    @pytest.mark.asyncio
    async def test_list_products_success(
        self, product_service, mock_repository, sample_product_doc
    ):
        """Test listing products with pagination"""
        # Arrange - Create mock cursor that returns synchronously
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[sample_product_doc])
        
        # find() should return cursor immediately (not async)
        mock_repository.collection.find = MagicMock(return_value=mock_cursor)
        mock_repository.collection.count_documents = AsyncMock(return_value=1)
        
        # Act
        products, total = await product_service.list_products(
            mock_repository.collection,
            skip=0,
            limit=10
        )
        
        # Assert
        assert len(products) == 1
        assert total == 1
        mock_repository.collection.find.assert_called_once()


class TestDaprPublishing(TestProductService):
    """Tests for Dapr event publishing methods"""
    
    @pytest.mark.asyncio
    async def test_publish_product_created(
        self, product_service, sample_product_doc
    ):
        """Test publishing product.created event"""
        # Arrange
        product_id = str(sample_product_doc["_id"])
        
        with patch('src.services.dapr_publisher.get_dapr_publisher') as mock_get_dapr:
            mock_publisher = AsyncMock()
            mock_publisher.publish_product_created = AsyncMock()
            mock_get_dapr.return_value = mock_publisher
            
            # Act
            await product_service._publish_product_created(
                product_id,
                sample_product_doc,
                "correlation-123"
            )
            
            # Assert
            mock_publisher.publish_product_created.assert_called_once()
            call_args = mock_publisher.publish_product_created.call_args[1]
            assert call_args["product"] == sample_product_doc
    
    @pytest.mark.asyncio
    async def test_publish_product_updated(
        self, product_service, sample_product_doc, admin_user
    ):
        """Test publishing product.updated event"""
        # Arrange
        product_id = str(sample_product_doc["_id"])
        changes = {"price": {"old": 29.99, "new": 39.99}}
        update_data = {**sample_product_doc, "price": 39.99}
        
        with patch('src.services.dapr_publisher.get_dapr_publisher') as mock_get_dapr:
            mock_publisher = AsyncMock()
            mock_publisher.publish_product_updated = AsyncMock()
            mock_get_dapr.return_value = mock_publisher
            
            # Act
            await product_service._publish_product_updated(
                product_id,
                changes,
                admin_user,
                update_data
            )
            
            # Assert
            mock_publisher.publish_product_updated.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_product_deleted(
        self, product_service, admin_user
    ):
        """Test publishing product.deleted event"""
        # Arrange
        with patch('src.services.dapr_publisher.get_dapr_publisher') as mock_get_dapr:
            mock_publisher = AsyncMock()
            mock_publisher.publish_product_deleted = AsyncMock()
            mock_get_dapr.return_value = mock_publisher
            
            # Act
            await product_service._publish_product_deleted(
                "507f1f77bcf86cd799439011",
                "TEST-001",
                admin_user,
                "correlation-123"
            )
            
            # Assert
            mock_publisher.publish_product_deleted.assert_called_once()
