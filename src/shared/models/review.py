from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.shared.validators.review_validators import ReviewValidatorMixin


class ReviewReport(BaseModel):
    reported_by: str
    reason: str
    reported_at: datetime = Field(default_factory=datetime.utcnow)


class Review(ReviewValidatorMixin, BaseModel):
    user_id: str
    username: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[str] = None
    reports: List[ReviewReport] = []
