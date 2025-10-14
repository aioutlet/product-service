from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.shared.validators.product_validators import ProductValidatorMixin


class ProductUpdate(ProductValidatorMixin, BaseModel):
    # Basic information
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    
    # Hierarchical category taxonomy
    department: Optional[str] = None      # Level 1: Women, Men, Kids, Electronics, Sports, Books
    category: Optional[str] = None        # Level 2: Clothing, Accessories, Computers, Audio, etc.
    subcategory: Optional[str] = None     # Level 3: Tops, Laptops, Headphones, Running, etc.
    product_type: Optional[str] = None    # Level 4: T-Shirts, Gaming Laptops, etc. (for filtering only)
    
    # Media and metadata
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, str]] = None
    variants: Optional[List[Dict[str, str]]] = None
    
    # Audit fields
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
