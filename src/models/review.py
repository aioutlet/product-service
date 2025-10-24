from datetime import datetime, UTC
from typing import List, Optional

from pydantic import BaseModel, Field

from src.validators.review_validators import ReviewValidatorMixin


def utc_now():
    """Helper function for Pydantic default_factory to get current UTC time"""
    return datetime.now(UTC)


class ReviewReport(BaseModel):
    reported_by: str
    reason: str
    reported_at: datetime = Field(default_factory=utc_now)


class Review(ReviewValidatorMixin, BaseModel):
    user_id: str
    username: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[str] = None
    reports: List[ReviewReport] = []
