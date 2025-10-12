"""Tests for review models"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.shared.models.review import Review, ReviewReport


class TestReviewModel:
    """Test Review model"""

    def test_review_dict_serialization(self):
        """Test that review can be serialized to dict"""
        review = Review(
            user_id="user123",
            username="testuser",
            rating=5,
            comment="Great product!"
        )
        review_dict = review.model_dump()
        
        assert review_dict["user_id"] == "user123"
        assert review_dict["username"] == "testuser"
        assert review_dict["rating"] == 5
        assert review_dict["comment"] == "Great product!"
        assert "created_at" in review_dict
        assert review_dict["updated_at"] is None
        assert review_dict["updated_by"] is None
        assert review_dict["reports"] == []

    def test_review_exclude_unset(self):
        """Test that exclude_unset only includes set fields"""
        review = Review(
            user_id="user123",
            username="testuser",
            rating=5
        )
        review_dict = review.model_dump(exclude_unset=True)
        
        assert "user_id" in review_dict
        assert "username" in review_dict
        assert "rating" in review_dict
        # These fields have default values but weren't explicitly set in exclude_unset mode
        # In Pydantic V2, default_factory fields are excluded when exclude_unset=True
        assert "comment" not in review_dict
        assert "updated_at" not in review_dict
        assert "updated_by" not in review_dict
        
    def test_review_json_serialization(self):
        """Test that review can be serialized to JSON"""
        review = Review(
            user_id="user123",
            username="testuser",
            rating=5,
            comment="Great product!"
        )
        json_str = review.model_dump_json()
        assert isinstance(json_str, str)
        assert "user123" in json_str
        assert "testuser" in json_str

    def test_review_from_dict(self):
        """Test creating review from dictionary"""
        review_data = {
            "user_id": "user123",
            "username": "testuser",
            "rating": 4,
            "comment": "Good product",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            "updated_by": None,
            "reports": []
        }
        review = Review(**review_data)
        assert review.user_id == "user123"
        assert review.rating == 4

    def test_review_update_tracking(self):
        """Test review update tracking fields"""
        review = Review(
            user_id="user123",
            username="testuser",
            rating=5,
            comment="Original comment"
        )
        
        # Initially no update tracking
        assert review.updated_at is None
        assert review.updated_by is None
        
        # Simulate an update
        review.updated_at = datetime.utcnow()
        review.updated_by = "admin456"
        review.comment = "Updated comment"
        
        assert review.updated_at is not None
        assert review.updated_by == "admin456"
        assert review.comment == "Updated comment"


class TestReviewReportModel:
    """Test ReviewReport model"""

    def test_review_report_creation(self):
        """Test creating a review report"""
        report = ReviewReport(
            reported_by="user456",
            reason="Inappropriate content"
        )
        
        assert report.reported_by == "user456"
        assert report.reason == "Inappropriate content"
        assert isinstance(report.reported_at, datetime)

    def test_review_report_dict_serialization(self):
        """Test that review report can be serialized to dict"""
        report = ReviewReport(
            reported_by="user456",
            reason="Spam"
        )
        report_dict = report.model_dump()
        
        assert report_dict["reported_by"] == "user456"
        assert report_dict["reason"] == "Spam"
        assert "reported_at" in report_dict

    def test_review_report_json_serialization(self):
        """Test that review report can be serialized to JSON"""
        report = ReviewReport(
            reported_by="user456",
            reason="Offensive language"
        )
        json_str = report.model_dump_json()
        assert isinstance(json_str, str)
        assert "user456" in json_str
        assert "Offensive language" in json_str

    def test_review_report_from_dict(self):
        """Test creating review report from dictionary"""
        report_data = {
            "reported_by": "moderator123",
            "reason": "Violation of terms",
            "reported_at": datetime.utcnow().isoformat()
        }
        report = ReviewReport(**report_data)
        assert report.reported_by == "moderator123"
        assert report.reason == "Violation of terms"

    def test_review_with_reports(self):
        """Test review with multiple reports"""
        report1 = ReviewReport(reported_by="user1", reason="Spam")
        report2 = ReviewReport(reported_by="user2", reason="Inappropriate")
        
        review = Review(
            user_id="user123",
            username="testuser", 
            rating=1,
            comment="Bad review",
            reports=[report1, report2]
        )
        
        assert len(review.reports) == 2
        assert review.reports[0].reported_by == "user1"
        assert review.reports[1].reason == "Inappropriate"