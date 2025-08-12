from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from src.validators.product_validators import ProductValidatorMixin

class ProductUpdate(ProductValidatorMixin, BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    # Removed in_stock field - inventory management is handled by inventory-service
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, str]] = None
    variants: Optional[List[Dict[str, str]]] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
