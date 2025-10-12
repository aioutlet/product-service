"""Tests for review controller"""
import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId

from src.api.controllers.review_controller import (
    list_reviews,
    add_review,
    update_review,
    delete_review,
    report_review
)
from src.shared.core.errors import ErrorResponse
from src.shared.models.review import Review, ReviewReport


class TestListReviews:
    """Test list_reviews function"""

    @pytest.mark.asyncio
    async def test_list_reviews_success(self, mock_collection, mock_product_doc, product_id):
        """Test successful listing of reviews"""
        mock_collection.find_one.return_value = mock_product_doc
        
        result = await list_reviews(product_id, mock_collection)
        
        assert len(result) == 2
        assert result[0]["user_id"] == "user123"
        assert result[1]["user_id"] == "user456"
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(product_id)})

    @pytest.mark.asyncio 
    async def test_list_reviews_product_not_found(self, mock_collection, product_id):
        """Test listing reviews when product doesn't exist"""
        mock_collection.find_one.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await list_reviews(product_id, mock_collection)
        
        assert exc_info.value.message == "Product not found"
        assert exc_info.value.status_code == 404


class TestAddReview:
    """Test add_review function"""

    @pytest.mark.asyncio
    async def test_add_review_success(self, mock_collection, sample_review, product_id):
        """Test successful addition of review"""
        mock_doc = {
            "_id": ObjectId(product_id),
            "name": "Test Product",
            "reviews": []
        }
        mock_collection.find_one.return_value = mock_doc
        mock_collection.update_one.return_value = AsyncMock()
        
        with patch('src.api.controllers.review_controller.logger') as mock_logger:
            result = await add_review(product_id, sample_review, mock_collection)
        
        assert result == sample_review
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(product_id)})
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_review_product_not_found(self, mock_collection, sample_review, product_id):
        """Test adding review when product doesn't exist"""
        mock_collection.find_one.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await add_review(product_id, sample_review, mock_collection)
        
        assert exc_info.value.message == "Product not found"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_add_review_user_already_reviewed(self, mock_collection, sample_review, product_id, mock_product_doc):
        """Test adding review when user has already reviewed"""
        mock_collection.find_one.return_value = mock_product_doc
        
        with pytest.raises(ErrorResponse) as exc_info:
            await add_review(product_id, sample_review, mock_collection)
        
        assert exc_info.value.message == "User has already reviewed this product"
        assert exc_info.value.status_code == 400


class TestUpdateReview:
    """Test update_review function"""

    @pytest.mark.asyncio
    async def test_update_review_success(self, mock_collection, product_id, mock_product_doc, acting_user):
        """Test successful review update"""
        mock_collection.find_one.return_value = mock_product_doc
        mock_collection.update_one.return_value = AsyncMock()
        
        updated_review = Review(
            user_id="user123",
            username="testuser",
            rating=4,
            comment="Updated comment"
        )
        
        with patch('src.api.controllers.review_controller.logger'):
            result = await update_review(product_id, "user123", updated_review, mock_collection, acting_user)
        
        assert result == updated_review
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(product_id)})
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_review_product_not_found(self, mock_collection, product_id, acting_user):
        """Test updating review when product doesn't exist"""
        mock_collection.find_one.return_value = None
        
        updated_review = Review(user_id="user123", username="testuser", rating=4)
        
        with pytest.raises(ErrorResponse) as exc_info:
            await update_review(product_id, "user123", updated_review, mock_collection, acting_user)
        
        assert exc_info.value.message == "Product not found"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_review_not_found(self, mock_collection, product_id, mock_product_doc, acting_user):
        """Test updating review that doesn't exist"""
        mock_collection.find_one.return_value = mock_product_doc
        
        updated_review = Review(user_id="nonexistent", username="nobody", rating=4)
        
        with pytest.raises(ErrorResponse) as exc_info:
            await update_review(product_id, "nonexistent", updated_review, mock_collection, acting_user)
        
        assert exc_info.value.message == "Review not found for this user"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_review_permission_denied(self, mock_collection, product_id, mock_product_doc):
        """Test updating review without permission"""
        mock_collection.find_one.return_value = mock_product_doc
        
        other_user = {
            "user_id": "user789",
            "username": "otheruser",
            "roles": ["user"]
        }
        
        updated_review = Review(user_id="user123", username="testuser", rating=4)
        
        with pytest.raises(ErrorResponse) as exc_info:
            await update_review(product_id, "user123", updated_review, mock_collection, other_user)
        
        assert exc_info.value.message == "You can only update your own review unless you are an admin."
        assert exc_info.value.status_code == 403


class TestDeleteReview:
    """Test delete_review function"""

    @pytest.mark.asyncio
    async def test_delete_review_success(self, mock_collection, product_id, mock_product_doc, acting_user):
        """Test successful review deletion"""
        mock_collection.find_one.return_value = mock_product_doc
        mock_collection.update_one.return_value = AsyncMock()
        
        with patch('src.api.controllers.review_controller.logger'):
            result = await delete_review(product_id, "user123", mock_collection, acting_user)
        
        assert result is None
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(product_id)})
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_review_product_not_found(self, mock_collection, product_id, acting_user):
        """Test deleting review when product doesn't exist"""
        mock_collection.find_one.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await delete_review(product_id, "user123", mock_collection, acting_user)
        
        assert exc_info.value.message == "Product not found"
        assert exc_info.value.status_code == 404


class TestReportReview:
    """Test report_review function"""

    @pytest.mark.asyncio
    async def test_report_review_success(self, mock_collection, product_id, mock_product_doc, sample_review_report, acting_user):
        """Test successful review reporting"""
        mock_collection.find_one.return_value = mock_product_doc
        mock_collection.update_one.return_value = AsyncMock()
        
        with patch('src.api.controllers.review_controller.logger'):
            result = await report_review(product_id, "user123", sample_review_report, mock_collection, acting_user)
        
        assert result == {"message": "Review reported"}
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(product_id)})
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_review_product_not_found(self, mock_collection, product_id, sample_review_report, acting_user):
        """Test reporting review when product doesn't exist"""
        mock_collection.find_one.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await report_review(product_id, "user123", sample_review_report, mock_collection, acting_user)
        
        assert exc_info.value.message == "Product not found"
        assert exc_info.value.status_code == 404