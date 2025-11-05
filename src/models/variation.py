"""
Product Variation Models

Defines models for parent-child product relationships and variant attributes.
Supports flexible variation types (size, color, style, etc.) with independent
or shared inventory management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class VariationType(str, Enum):
    """Product variation type."""
    PARENT = "parent"      # Parent product with children
    CHILD = "child"        # Child variant of a parent
    STANDALONE = "standalone"  # Independent product (no variations)


class InventoryMode(str, Enum):
    """Inventory management mode for variations."""
    INDEPENDENT = "independent"  # Each child has its own inventory
    SHARED = "shared"            # All children share parent's inventory


class VariantAttribute(BaseModel):
    """A single variant attribute (e.g., color: red)."""
    name: str = Field(..., description="Attribute name (e.g., 'color', 'size')")
    value: str = Field(..., description="Attribute value (e.g., 'red', 'XL')")
    display_name: Optional[str] = Field(None, description="User-friendly display name")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure attribute name is lowercase."""
        return v.lower().strip()


class VariantAttributeOption(BaseModel):
    """Available option for a variant attribute."""
    value: str = Field(..., description="Option value")
    display_name: Optional[str] = Field(None, description="Display name")
    is_available: bool = Field(True, description="Whether this option is currently available")
    additional_price: float = Field(0.0, description="Additional price for this option")


class VariantAttributeDefinition(BaseModel):
    """Definition of a variant attribute for parent products."""
    name: str = Field(..., description="Attribute name (e.g., 'color', 'size')")
    display_name: str = Field(..., description="User-friendly display name")
    options: List[VariantAttributeOption] = Field(
        default_factory=list,
        description="Available options for this attribute"
    )
    is_required: bool = Field(True, description="Whether customer must select this attribute")
    display_order: int = Field(0, description="Order in which to display this attribute")


class VariationConfiguration(BaseModel):
    """Configuration for product variations."""
    inventory_mode: InventoryMode = Field(
        InventoryMode.INDEPENDENT,
        description="How inventory is managed for variations"
    )
    variant_attributes: List[VariantAttributeDefinition] = Field(
        default_factory=list,
        description="Definitions for variant attributes"
    )
    allow_mixed_cart: bool = Field(
        True,
        description="Allow multiple variants in same cart"
    )
    default_variant_id: Optional[str] = Field(
        None,
        description="Default child product to display"
    )


class CreateVariationRequest(BaseModel):
    """Request to create a child variation."""
    parent_id: str = Field(..., description="Parent product ID")
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0, description="Override parent price")
    compare_at_price: Optional[float] = Field(None, gt=0)
    variant_attributes: List[VariantAttribute] = Field(
        ...,
        min_length=1,
        description="Variant attributes (e.g., color=red, size=XL)"
    )
    description: Optional[str] = None
    images: Optional[List[Dict]] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: bool = True


class UpdateVariationRequest(BaseModel):
    """Request to update a child variation."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    variant_attributes: Optional[List[VariantAttribute]] = None
    description: Optional[str] = None
    images: Optional[List[Dict]] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class VariantAttributeMatrix(BaseModel):
    """Matrix showing all variant combinations and their availability."""
    attribute_names: List[str] = Field(..., description="Names of variant attributes")
    combinations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All possible combinations with availability and pricing"
    )


class ProductVariationSummary(BaseModel):
    """Summary of a product's variations."""
    product_id: str
    product_name: str
    variation_type: VariationType
    parent_id: Optional[str] = None
    child_count: int = 0
    available_child_count: int = 0
    variant_attributes: List[VariantAttribute] = Field(default_factory=list)
    price_range: Optional[Dict[str, float]] = None  # {"min": 10.0, "max": 50.0}
    inventory_mode: Optional[InventoryMode] = None


class VariationRelationship(BaseModel):
    """Represents the relationship between parent and child products."""
    parent: ProductVariationSummary
    children: List[ProductVariationSummary]
    variation_config: Optional[VariationConfiguration] = None
    attribute_matrix: Optional[VariantAttributeMatrix] = None


class BulkCreateVariationsRequest(BaseModel):
    """Request to create multiple variations at once."""
    parent_id: str = Field(..., description="Parent product ID")
    variations: List[CreateVariationRequest] = Field(
        ...,
        min_length=1,
        description="List of variations to create"
    )
    auto_generate_names: bool = Field(
        False,
        description="Auto-generate names from parent + attributes"
    )


class VariationValidationError(BaseModel):
    """Validation error for a variation."""
    field: str
    message: str
    variation_index: Optional[int] = None


class BulkCreateVariationsResponse(BaseModel):
    """Response from bulk variation creation."""
    success_count: int
    failure_count: int
    created_ids: List[str] = Field(default_factory=list)
    errors: List[VariationValidationError] = Field(default_factory=list)
