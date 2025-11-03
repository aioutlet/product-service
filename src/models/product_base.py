from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.validators.product_validators import ProductValidatorMixin


def utc_now():
    """Helper function for Pydantic default_factory to get current UTC time"""
    return datetime.now(UTC)


class ProductHistoryEntry(BaseModel):
    updated_by: str
    updated_at: datetime
    changes: Dict[str, str]  # field: new_value


class ReviewAggregates(BaseModel):
    """Denormalized review data from Review Service (REQ-3.2.1)"""
    average_rating: float = 0.0  # 1-5 stars, decimal precision
    total_reviews: int = 0
    verified_purchase_count: int = 0
    rating_distribution: Dict[str, int] = {
        "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
    }


class InventoryStatus(BaseModel):
    """Denormalized inventory data from Inventory Service (REQ-3.2.2)"""
    availability: str = "unknown"  # in_stock, low_stock, out_of_stock, pre_order, discontinued
    available_quantity: int = 0
    low_stock_threshold: int = 10
    last_updated: Optional[datetime] = None


class ProductBadge(BaseModel):
    """Product badges for marketing (REQ-3.2.3)"""
    badge_type: str  # best-seller, trending, hot-deal
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    auto_assigned: bool = True
    criteria: Dict[str, Any] = {}


class QAStats(BaseModel):
    """Denormalized Q&A stats from Q&A Service (REQ-3.2.4)"""
    total_questions: int = 0
    answered_questions: int = 0
    last_updated: Optional[datetime] = None


class ProductBase(ProductValidatorMixin, BaseModel):
    # Basic information
    name: str
    description: Optional[str] = None
    price: float
    brand: Optional[str] = None
    sku: Optional[str] = None
    
    # Hierarchical category taxonomy (flat structure for better query performance)
    department: Optional[str] = None      # Level 1: Women, Men, Kids, Electronics, Sports, Books
    category: Optional[str] = None        # Level 2: Clothing, Accessories, Computers, Audio, etc.
    subcategory: Optional[str] = None     # Level 3: Tops, Laptops, Headphones, Running, etc.
    product_type: Optional[str] = None    # Level 4: T-Shirts, Gaming Laptops, etc. (for filtering only)
    
    # Media and metadata
    images: List[str] = []
    tags: List[str] = []
    
    # Product variations
    colors: List[str] = []  # Available colors: ["Red", "Blue", "Black"]
    sizes: List[str] = []   # Available sizes: ["S", "M", "L", "XL"]
    
    # Product specifications (flexible key-value pairs)
    specifications: Dict[str, str] = {}
    
    # Denormalized data from other services (REQ-3.2.x - Event Consumption)
    review_aggregates: ReviewAggregates = Field(default_factory=ReviewAggregates)
    inventory_status: InventoryStatus = Field(default_factory=InventoryStatus)
    badges: List[ProductBadge] = []
    qa_stats: QAStats = Field(default_factory=QAStats)
    
    # Audit trail
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True  # for soft delete
    history: List[ProductHistoryEntry] = []  # audit log
