from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from .review import Review
from src.validators.product_validators import ProductValidatorMixin

class ProductHistoryEntry(BaseModel):
    updated_by: str
    updated_at: datetime
    changes: Dict[str, str]  # field: new_value

class ProductBase(ProductValidatorMixin, BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    in_stock: int
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    images: List[str] = []
    tags: List[str] = []
    attributes: Dict[str, str] = {}
    variants: List[Dict[str, str]] = []
    average_rating: float = 0
    num_reviews: int = 0
    reviews: List[Review] = []
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True  # for soft delete
    history: List[ProductHistoryEntry] = []  # audit log
