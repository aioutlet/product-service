"""
Integration tests for Product Controller Event Publishing
Tests PRD REQ-3.1.x: Event Publishing from product operations
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.controllers.product_controller import (
    create_product,
    update_product,
    delete_product
)
from src.models.product import ProductCreate, ProductUpdate


class TestProductControllerEventPublishing:
    """Test suite for event publishing in product controller operations"""

    @pytest.fixture
    def mock_collection(self):
        """Mock MongoDB collection"""
        collection = MagicMock()
        collection.find_one = AsyncMock()
        collection.insert_one = AsyncMock()
        collection.update_one = AsyncMock()
        return collection

    @pytest.fixture
    def mock_dapr_publisher(self):
        """Mock Dapr publisher"""
        with patch(
            'src.controllers.product_controller.get_dapr_publisher'
        ) as mock:
            publisher = MagicMock()
            publisher.publish = AsyncMock()
            mock.return_value = publisher
            yield publisher

    @pytest.fixture
    def sample_product_create(self):
        """Sample product create data"""
        return ProductCreate(
            name="Test Product",
            description="Test Description",
            price=99.99,
            sku="TEST-SKU-001",
            brand="TestBrand",
            department="Electronics",
            category="Computers",
            created_by="test-user"
        )

    @pytest.fixture
    def sample_product_update(self):
        """Sample product update data"""
        return ProductUpdate(
            name="Updated Product",
            price=149.99
        )

    @pytest.fixture
    def mock_acting_user(self):
        """Mock user with admin role"""
        user = MagicMock()
        user.user_id = "admin-123"
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_create_product_publishes_created_event(
        self,
        mock_collection,
        mock_dapr_publisher,
        sample_product_create,
        mock_acting_user
    ):
        """Test that creating product publishes product.created event"""
        # Arrange
        mock_collection.find_one.side_effect = [
            None,  # No existing SKU
            {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Test Product",
                "price": 99.99,
                "sku": "TEST-SKU-001",
                "department": "Electronics",
                "category": "Computers",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
        ]
        mock_collection.insert_one.return_value.inserted_id = (
            "507f1f77bcf86cd799439011"
        )

        # Act
        await create_product(
            sample_product_create,
            mock_collection,
            mock_acting_user
        )

        # Assert
        assert mock_dapr_publisher.publish.called
        call_args = mock_dapr_publisher.publish.call_args
        assert call_args[1]['event_type'] == 'product.created'
        assert call_args[1]['data']['productId'] == "507f1f77bcf86cd799439011"
        assert call_args[1]['data']['name'] == "Test Product"
        assert call_args[1]['data']['price'] == 99.99
        assert call_args[1]['data']['sku'] == "TEST-SKU-001"
        assert 'createdAt' in call_args[1]['data']

    @pytest.mark.asyncio
    async def test_create_product_continues_on_event_publish_failure(
        self,
        mock_collection,
        mock_dapr_publisher,
        sample_product_create,
        mock_acting_user
    ):
        """Test that product creation continues if event publishing fails"""
        # Arrange
        mock_collection.find_one.side_effect = [
            None,  # No existing SKU
            {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Test Product",
                "price": 99.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
        ]
        mock_collection.insert_one.return_value.inserted_id = (
            "507f1f77bcf86cd799439011"
        )
        mock_dapr_publisher.publish.side_effect = Exception(
            "Event publishing failed"
        )

        # Act - should not raise exception
        result = await create_product(
            sample_product_create,
            mock_collection,
            mock_acting_user
        )

        # Assert - product was created despite event failure
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439011"

    @pytest.mark.asyncio
    async def test_update_product_publishes_updated_event(
        self,
        mock_collection,
        mock_dapr_publisher,
        sample_product_update,
        mock_acting_user
    ):
        """Test that updating product publishes product.updated event"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_collection.find_one.side_effect = [
            {
                "_id": product_id,
                "name": "Old Product",
                "price": 99.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "_id": product_id,
                "name": "Updated Product",
                "price": 149.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
        ]
        mock_collection.update_one.return_value.matched_count = 1

        # Act
        with patch(
            'src.controllers.product_controller.validate_object_id',
            return_value=product_id
        ):
            await update_product(
                product_id,
                sample_product_update,
                mock_collection,
                mock_acting_user
            )

        # Assert
        assert mock_dapr_publisher.publish.call_count >= 1
        # Find the product.updated call
        updated_calls = [
            call for call in mock_dapr_publisher.publish.call_args_list
            if call[1]['event_type'] == 'product.updated'
        ]
        assert len(updated_calls) > 0
        call_args = updated_calls[0]
        assert call_args[1]['data']['productId'] == product_id
        assert 'updatedFields' in call_args[1]['data']

    @pytest.mark.asyncio
    async def test_update_product_price_publishes_price_changed_event(
        self,
        mock_collection,
        mock_dapr_publisher,
        mock_acting_user
    ):
        """Test that updating price publishes product.price.changed event"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        price_update = ProductUpdate(price=149.99)
        mock_collection.find_one.side_effect = [
            {
                "_id": product_id,
                "name": "Test Product",
                "price": 99.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "_id": product_id,
                "name": "Test Product",
                "price": 149.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
        ]
        mock_collection.update_one.return_value.matched_count = 1

        # Act
        with patch(
            'src.controllers.product_controller.validate_object_id',
            return_value=product_id
        ):
            await update_product(
                product_id,
                price_update,
                mock_collection,
                mock_acting_user
            )

        # Assert - should publish both updated and price.changed events
        assert mock_dapr_publisher.publish.call_count >= 2
        # Find the product.price.changed call
        price_calls = [
            call for call in mock_dapr_publisher.publish.call_args_list
            if call[1]['event_type'] == 'product.price.changed'
        ]
        assert len(price_calls) > 0
        call_args = price_calls[0]
        assert call_args[1]['data']['productId'] == product_id
        assert call_args[1]['data']['oldPrice'] == 99.99
        assert call_args[1]['data']['newPrice'] == 149.99

    @pytest.mark.asyncio
    async def test_delete_product_publishes_deleted_event(
        self,
        mock_collection,
        mock_dapr_publisher,
        mock_acting_user
    ):
        """Test that deleting product publishes product.deleted event"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_collection.find_one.return_value = {
            "_id": product_id,
            "name": "Test Product",
            "is_active": True
        }
        mock_collection.update_one.return_value.matched_count = 1

        # Act
        with patch(
            'src.controllers.product_controller.validate_object_id',
            return_value=product_id
        ):
            await delete_product(
                product_id,
                mock_collection,
                mock_acting_user
            )

        # Assert
        assert mock_dapr_publisher.publish.called
        call_args = mock_dapr_publisher.publish.call_args
        assert call_args[1]['event_type'] == 'product.deleted'
        assert call_args[1]['data']['productId'] == product_id
        assert call_args[1]['data']['softDelete'] is True
        assert call_args[1]['data']['deletedBy'] == mock_acting_user.user_id

    @pytest.mark.asyncio
    async def test_delete_product_continues_on_event_publish_failure(
        self,
        mock_collection,
        mock_dapr_publisher,
        mock_acting_user
    ):
        """Test that product deletion continues if event publishing fails"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        mock_collection.find_one.return_value = {
            "_id": product_id,
            "name": "Test Product",
            "is_active": True
        }
        mock_collection.update_one.return_value.matched_count = 1
        mock_dapr_publisher.publish.side_effect = Exception(
            "Event publishing failed"
        )

        # Act - should not raise exception
        with patch(
            'src.controllers.product_controller.validate_object_id',
            return_value=product_id
        ):
            result = await delete_product(
                product_id,
                mock_collection,
                mock_acting_user
            )

        # Assert - deletion completed despite event failure
        assert result is None
        assert mock_collection.update_one.called

    @pytest.mark.asyncio
    async def test_update_product_without_price_does_not_publish_price_event(
        self,
        mock_collection,
        mock_dapr_publisher,
        mock_acting_user
    ):
        """Test that updating non-price fields doesn't publish price event"""
        # Arrange
        product_id = "507f1f77bcf86cd799439011"
        name_update = ProductUpdate(name="New Name")
        mock_collection.find_one.side_effect = [
            {
                "_id": product_id,
                "name": "Old Name",
                "price": 99.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            },
            {
                "_id": product_id,
                "name": "New Name",
                "price": 99.99,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "history": []
            }
        ]
        mock_collection.update_one.return_value.matched_count = 1

        # Act
        with patch(
            'src.controllers.product_controller.validate_object_id',
            return_value=product_id
        ):
            await update_product(
                product_id,
                name_update,
                mock_collection,
                mock_acting_user
            )

        # Assert - should only publish product.updated, not price.changed
        price_calls = [
            call for call in mock_dapr_publisher.publish.call_args_list
            if call[1]['event_type'] == 'product.price.changed'
        ]
        assert len(price_calls) == 0
