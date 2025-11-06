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