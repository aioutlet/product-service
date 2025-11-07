"""
Base Product model with validation and common fields
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now():
    """Helper function for Pydantic default_factory to get current UTC time"""
    return datetime.now(timezone.utc)


class ProductHistoryEntry(BaseModel):
    """Model for tracking product change history"""
    updated_by: str
    updated_at: datetime
    changes: Dict[str, str]  # field: new_value


class RatingDistribution(BaseModel):
    """Model for rating distribution breakdown"""
    five_star: int = Field(default=0, alias="5")
    four_star: int = Field(default=0, alias="4")
    three_star: int = Field(default=0, alias="3")
    two_star: int = Field(default=0, alias="2")
    one_star: int = Field(default=0, alias="1")
    
    class Config:
        populate_by_name = True


class ReviewAggregates(BaseModel):
    """Model for aggregated review statistics"""
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    total_review_count: int = Field(default=0, ge=0)
    verified_review_count: int = Field(default=0, ge=0)
    rating_distribution: RatingDistribution = Field(default_factory=RatingDistribution)
    recent_reviews: List[str] = Field(default_factory=list, max_length=5)
    last_review_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=utc_now)


class ProductBase(BaseModel):
    """Base Product model with all common fields"""
    
    # Basic information
    name: str
    description: Optional[str] = None
    price: float
    brand: Optional[str] = None
    sku: Optional[str] = None
    
    # Hierarchical category taxonomy
    department: Optional[str] = None      # Level 1: Women, Men, Kids, Electronics
    category: Optional[str] = None        # Level 2: Clothing, Accessories, Computers
    subcategory: Optional[str] = None     # Level 3: Tops, Laptops, Headphones
    product_type: Optional[str] = None    # Level 4: T-Shirts, Gaming Laptops
    
    # Media and metadata
    images: List[str] = []
    tags: List[str] = []
    
    # Product variations
    colors: List[str] = []
    sizes: List[str] = []
    
    # Product specifications
    specifications: Dict[str, str] = {}
    
    # Review aggregates
    review_aggregates: ReviewAggregates = Field(default_factory=ReviewAggregates)
    
    # Audit trail
    created_by: str = "system"
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True
    history: List[ProductHistoryEntry] = []


class Product(ProductBase):
    """Product model with ID for database operations"""
    id: Optional[str] = None