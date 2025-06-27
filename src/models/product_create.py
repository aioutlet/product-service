from .product_base import ProductBase
from src.validators.product_validators import ProductCreateValidatorMixin

class ProductCreate(ProductCreateValidatorMixin, ProductBase):
    pass
