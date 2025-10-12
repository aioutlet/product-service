from src.shared.validators.product_validators import ProductCreateValidatorMixin

from .product_base import ProductBase


class ProductCreate(ProductCreateValidatorMixin, ProductBase):
    pass
