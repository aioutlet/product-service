from .product_base import ProductBase

class ProductDB(ProductBase):
    id: str

    class Config:
        from_attributes = True
