from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.shared.validators.product_validators import ProductValidatorMixin


class ProductHistoryEntry(BaseModel):
    updated_by: str
    updated_at: datetime
    changes: Dict[str, str]  # field: new_value


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
    
    # Reviews and ratings (aggregate data only - individual reviews managed by review-service)
    average_rating: float = 0
    num_reviews: int = 0
    # NOTE: Individual reviews are NOT stored here - they are managed by the review-service
    
    # Audit trail
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True  # for soft delete
    history: List[ProductHistoryEntry] = []  # audit log
