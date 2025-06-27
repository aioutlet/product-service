from pydantic import RootModel, BaseModel
from typing import List
from .product_base import ProductBase
from .product_create import ProductCreate
from .product_update import ProductUpdate
from .product_db import ProductDB

# Product Pydantic models and DB schemas

class ProductSearchResponse(BaseModel):
    """Response model for product search with pagination metadata"""
    products: List[ProductDB]
    total_count: int
    current_page: int
    total_pages: int

class Product(RootModel[ProductBase]):
    pass

class ProductInCreate(RootModel[ProductCreate]):
    pass

class ProductInUpdate(RootModel[ProductUpdate]):
    pass

class ProductInDB(RootModel[ProductDB]):
    class Config:
        from_attributes = True
