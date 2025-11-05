from bson.errors import InvalidId
from bson.objectid import ObjectId
from pydantic import field_validator


def validate_object_id(value: str) -> ObjectId:
    """
    Validate and convert a string to MongoDB ObjectId.
    
    Args:
        value: String representation of ObjectId
        
    Returns:
        ObjectId: Valid MongoDB ObjectId
        
    Raises:
        ValueError: If the value is not a valid ObjectId format
    """
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError("Invalid ObjectId format.")


class ProductValidatorMixin:
    @field_validator("name")
    @classmethod
    def name_valid(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Product name cannot be empty")
        if v is not None and (len(v) < 1 or len(v) > 100):
            raise ValueError("Product name must be between 1 and 100 characters")
        return v

    @field_validator("price")
    @classmethod
    def price_valid(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    # Removed in_stock validator - inventory management is handled by inventory-service

    @field_validator("category")
    @classmethod
    def category_valid(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("Category name must be up to 100 characters")
        return v

    @field_validator("brand")
    @classmethod
    def brand_valid(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("Brand name must be up to 100 characters")
        return v

    @field_validator("sku")
    @classmethod
    def sku_valid(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("SKU must be up to 100 characters")
        return v

    @field_validator("description")
    @classmethod
    def description_valid(cls, v):
        if v is not None and len(v) > 5000:
            raise ValueError("Description can be up to 5000 characters")
        return v


class ProductCreateValidatorMixin:
    @field_validator("created_by")
    @classmethod
    def created_by_required(cls, v):
        if not v or not v.strip():
            raise ValueError("User ID of the creator is required")
        return v
