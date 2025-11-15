"""Unit tests for event consumers"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.events.consumers.review_consumer import ReviewEventConsumer


class TestReviewEventConsumer:
    """Test ReviewEventConsumer for handling review events"""

    def setup_method(self):
        """Set up test fixtures"""
        self.consumer = ReviewEventConsumer()
        self.consumer.product_repo = AsyncMock()
        self.consumer.processed_events_repo = AsyncMock()
        self.consumer.db = Mock()

    @pytest.mark.asyncio
    async def test_handle_review_created_success(self):
        """Test successful handling of review.created event"""
        # Arrange
        event_data = {
            "id": "event-123",
            "metadata": {"correlationId": "corr-123"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 5,
                "isVerifiedPurchase": True,
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Mock product with existing aggregates
        mock_product = {
            "review_aggregates": {
                "total_review_count": 2,
                "verified_review_count": 1,
                "average_rating": 4.0,
                "rating_distribution": {"5": 1, "4": 0, "3": 1, "2": 0, "1": 0},
                "recent_reviews": ["old-review-1", "old-review-2"]
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.return_value = mock_product
        self.consumer.product_repo.update.return_value = None
        self.consumer.processed_events_repo.mark_processed.return_value = None

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "success"
        self.consumer.processed_events_repo.is_processed.assert_called_once_with("event-123")
        self.consumer.product_repo.get_by_id.assert_called_once_with("prod-123")
        self.consumer.product_repo.update.assert_called_once()
        self.consumer.processed_events_repo.mark_processed.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_review_created_already_processed(self):
        """Test handling of already processed event (idempotency)"""
        # Arrange
        event_data = {
            "id": "event-123",
            "data": {"productId": "prod-123", "reviewId": "review-123", "rating": 5}
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = True

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "success"
        assert "Already processed" in result["message"]
        self.consumer.product_repo.get_by_id.assert_not_called()
        self.consumer.product_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_review_created_missing_event_id(self):
        """Test handling event without event ID"""
        # Arrange
        event_data = {
            "data": {"productId": "prod-123", "reviewId": "review-123", "rating": 5}
        }

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "error"
        assert "Missing event ID" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_review_created_missing_required_fields(self):
        """Test handling event with missing required fields"""
        # Arrange
        event_data = {
            "id": "event-123",
            "metadata": {"correlationId": "corr-123"},
            "data": {
                "productId": "prod-123",
                # Missing reviewId and rating
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "error"
        assert "Missing required fields" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_review_created_product_not_found(self):
        """Test handling event for non-existent product"""
        # Arrange
        event_data = {
            "id": "event-123",
            "metadata": {"correlationId": "corr-123"},
            "data": {
                "productId": "nonexistent",
                "reviewId": "review-123",
                "rating": 5
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.return_value = None

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "error"
        assert "Product not found" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_review_created_calculates_average_correctly(self):
        """Test that average rating is calculated correctly"""
        # Arrange
        event_data = {
            "id": "event-123",
            "metadata": {"correlationId": "corr-123"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 3,
                "isVerifiedPurchase": False,
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        # Current: 2 reviews, avg 4.0 (total: 8.0)
        # Adding: 1 review, rating 3
        # Expected: (8.0 + 3) / 3 = 3.67
        mock_product = {
            "review_aggregates": {
                "total_review_count": 2,
                "verified_review_count": 1,
                "average_rating": 4.0,
                "rating_distribution": {"5": 0, "4": 2, "3": 0, "2": 0, "1": 0},
                "recent_reviews": []
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.return_value = mock_product
        
        # Capture the update call
        update_calls = []
        async def capture_update(product_id, update_data):
            update_calls.append((product_id, update_data))
        self.consumer.product_repo.update.side_effect = capture_update
        self.consumer.processed_events_repo.mark_processed.return_value = None

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "success"
        assert len(update_calls) == 1
        _, update_data = update_calls[0]
        assert "review_aggregates" in update_data
        aggregates = update_data["review_aggregates"]
        assert aggregates["average_rating"] == 3.67
        assert aggregates["total_review_count"] == 3
        assert aggregates["rating_distribution"]["3"] == 1

    @pytest.mark.asyncio
    async def test_handle_review_updated_success(self):
        """Test successful handling of review.updated event"""
        # Arrange
        event_data = {
            "id": "event-456",
            "metadata": {"correlationId": "corr-456"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 5,
                "previousRating": 3
            }
        }
        
        mock_product = {
            "review_aggregates": {
                "total_review_count": 3,
                "average_rating": 4.0,
                "rating_distribution": {"5": 1, "4": 0, "3": 2, "2": 0, "1": 0},
                "recent_reviews": []
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.return_value = mock_product
        self.consumer.product_repo.update.return_value = None
        self.consumer.processed_events_repo.mark_processed.return_value = None

        # Act
        result = await self.consumer.handle_review_updated(event_data)

        # Assert
        assert result["status"] == "success"
        self.consumer.product_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_review_updated_rating_unchanged(self):
        """Test handling of updated event where rating didn't change"""
        # Arrange
        event_data = {
            "id": "event-456",
            "metadata": {"correlationId": "corr-456"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 4,
                "previousRating": 4
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False

        # Act
        result = await self.consumer.handle_review_updated(event_data)

        # Assert
        assert result["status"] == "success"
        assert "Rating unchanged" in result["message"]
        self.consumer.product_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_review_deleted_success(self):
        """Test successful handling of review.deleted event"""
        # Arrange
        event_data = {
            "id": "event-789",
            "metadata": {"correlationId": "corr-789"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 5,
                "isVerifiedPurchase": True
            }
        }
        
        mock_product = {
            "review_aggregates": {
                "total_review_count": 3,
                "verified_review_count": 2,
                "average_rating": 4.67,  # (5 + 5 + 4) / 3
                "rating_distribution": {"5": 2, "4": 1, "3": 0, "2": 0, "1": 0},
                "recent_reviews": ["review-123", "review-456"]
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.return_value = mock_product
        self.consumer.product_repo.update.return_value = None
        self.consumer.processed_events_repo.mark_processed.return_value = None

        # Act
        result = await self.consumer.handle_review_deleted(event_data)

        # Assert
        assert result["status"] == "success"
        self.consumer.product_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_review_deleted_last_review(self):
        """Test deleting the last review (average becomes 0)"""
        # Arrange
        event_data = {
            "id": "event-789",
            "metadata": {"correlationId": "corr-789"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 5,
                "isVerifiedPurchase": False
            }
        }
        
        mock_product = {
            "review_aggregates": {
                "total_review_count": 1,
                "verified_review_count": 0,
                "average_rating": 5.0,
                "rating_distribution": {"5": 1, "4": 0, "3": 0, "2": 0, "1": 0},
                "recent_reviews": ["review-123"]
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.return_value = mock_product
        
        # Capture the update call
        update_calls = []
        async def capture_update(product_id, update_data):
            update_calls.append((product_id, update_data))
        self.consumer.product_repo.update.side_effect = capture_update
        self.consumer.processed_events_repo.mark_processed.return_value = None

        # Act
        result = await self.consumer.handle_review_deleted(event_data)

        # Assert
        assert result["status"] == "success"
        assert len(update_calls) == 1
        _, update_data = update_calls[0]
        aggregates = update_data["review_aggregates"]
        assert aggregates["average_rating"] == 0.0
        assert aggregates["total_review_count"] == 0
        assert len(aggregates["recent_reviews"]) == 0

    @pytest.mark.asyncio
    async def test_handle_review_created_exception(self):
        """Test exception handling in review.created handler"""
        # Arrange
        event_data = {
            "id": "event-123",
            "metadata": {"correlationId": "corr-123"},
            "data": {
                "productId": "prod-123",
                "reviewId": "review-123",
                "rating": 5
            }
        }
        
        self.consumer.processed_events_repo.is_processed.return_value = False
        self.consumer.product_repo.get_by_id.side_effect = Exception("Database error")

        # Act
        result = await self.consumer.handle_review_created(event_data)

        # Assert
        assert result["status"] == "error"
        assert "Database error" in result["message"]
