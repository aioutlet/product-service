"""
API schemas for Product endpoints following FastAPI best practices
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.product import ProductBase, ProductHistoryEntry


class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., ge=0)
    brand: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    
    # Hierarchical category taxonomy
    department: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=100)
    
    # Media and metadata
    images: List[str] = []
    tags: List[str] = []
    
    # Product variations
    colors: List[str] = []
    sizes: List[str] = []
    
    # Product specifications
    specifications: dict = {}


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, ge=0)
    brand: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    
    # Hierarchical category taxonomy
    department: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=100)
    
    # Media and metadata
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    # Product variations
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    
    # Product specifications
    specifications: Optional[dict] = None


class ProductResponse(ProductBase):
    """Schema for product responses including all fields"""
    id: str
    
    class Config:
        from_attributes = True


class ProductSearchResponse(BaseModel):
    """Response schema for product search with pagination"""
    products: List[ProductResponse]
    total_count: int
    current_page: int
    total_pages: int


class ProductStatsResponse(BaseModel):
    """Response schema for admin product statistics"""
    total: int
    active: int