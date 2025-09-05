"""Tests for review validators"""
import pytest
from pydantic import ValidationError

from src.models.review import Review, ReviewReport


class TestReviewValidators:
    """Test review validation logic"""

    def test_valid_review_creation(self):
        """Test creating a valid review"""
        review_data = {
            "user_id": "user123",
            "username": "testuser",
            "rating": 5,
            "comment": "Great product!"
        }
        review = Review(**review_data)
        assert review.user_id == "user123"
        assert review.username == "testuser"
        assert review.rating == 5
        assert review.comment == "Great product!"

    def test_user_id_required(self):
        """Test that user_id is required and cannot be empty"""
        # Test missing user_id
        with pytest.raises(ValidationError) as exc_info:
            Review(username="testuser", rating=5)
        assert "Field required" in str(exc_info.value)

        # Test empty user_id
        with pytest.raises(ValidationError) as exc_info:
            Review(user_id="", username="testuser", rating=5)
        assert "User ID is required for a review" in str(exc_info.value)

        # Test whitespace-only user_id
        with pytest.raises(ValidationError) as exc_info:
            Review(user_id="   ", username="testuser", rating=5)
        assert "User ID is required for a review" in str(exc_info.value)

    def test_username_required(self):
        """Test that username is required and cannot be empty"""
        # Test missing username
        with pytest.raises(ValidationError) as exc_info:
            Review(user_id="user123", rating=5)
        assert "Field required" in str(exc_info.value)

        # Test empty username
        with pytest.raises(ValidationError) as exc_info:
            Review(user_id="user123", username="", rating=5)
        assert "Username is required for a review" in str(exc_info.value)

        # Test whitespace-only username
        with pytest.raises(ValidationError) as exc_info:
            Review(user_id="user123", username="   ", rating=5)
        assert "Username is required for a review" in str(exc_info.value)

    def test_rating_validation(self):
        """Test rating validation (must be between 1 and 5)"""
        # Test valid ratings
        for rating in [1, 2, 3, 4, 5]:
            review = Review(user_id="user123", username="testuser", rating=rating)
            assert review.rating == rating

        # Test invalid ratings
        invalid_ratings = [0, -1, 6, 10, -5]
        for rating in invalid_ratings:
            with pytest.raises(ValidationError) as exc_info:
                Review(user_id="user123", username="testuser", rating=rating)
            assert "Rating must be between 1 and 5" in str(exc_info.value)

    def test_comment_validation(self):
        """Test comment length validation (max 1000 characters)"""
        # Test valid comment
        valid_comment = "This is a valid comment"
        review = Review(user_id="user123", username="testuser", rating=5, comment=valid_comment)
        assert review.comment == valid_comment

        # Test None comment (should be allowed)
        review = Review(user_id="user123", username="testuser", rating=5, comment=None)
        assert review.comment is None

        # Test comment that's exactly at the limit
        max_comment = "a" * 1000
        review = Review(user_id="user123", username="testuser", rating=5, comment=max_comment)
        assert review.comment == max_comment

        # Test comment that exceeds limit
        with pytest.raises(ValidationError) as exc_info:
            Review(user_id="user123", username="testuser", rating=5, comment="a" * 1001)
        assert "Comment can be up to 1000 characters" in str(exc_info.value)

    def test_review_report_creation(self):
        """Test creating a valid review report"""
        report_data = {
            "reported_by": "user456",
            "reason": "Spam content"
        }
        report = ReviewReport(**report_data)
        assert report.reported_by == "user456"
        assert report.reason == "Spam content"
        assert report.reported_at is not None

    def test_review_with_default_values(self):
        """Test that review has proper default values"""
        review = Review(user_id="user123", username="testuser", rating=5)
        assert review.created_at is not None
        assert review.updated_at is None
        assert review.updated_by is None
        assert review.reports == []