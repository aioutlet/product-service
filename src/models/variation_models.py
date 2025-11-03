"""
Product Variation Models
Implements PRD REQ-8.1 to REQ-8.5: Product Variations (Parent-Child Relationships)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class VariationTheme(str, Enum):
    """
    Variation themes supported by the system (REQ-8.1)
    """
    # Single dimension
    COLOR = "color"
    SIZE = "size"
    STYLE = "style"
    MATERIAL = "material"
    SCENT = "scent"
    FLAVOR = "flavor"
    
    # Two dimension
    COLOR_SIZE = "color-size"
    STYLE_COLOR = "style-color"
    SIZE_MATERIAL = "size-material"
    COLOR_MATERIAL = "color-material"
    
    # Custom
    CUSTOM = "custom"


class VariationAttribute(BaseModel):
    """
    Single variation attribute (REQ-8.2)
    """
    name: str = Field(..., description="Attribute name (e.g., 'Color', 'Size')")
    display_name: str = Field(
        ...,
        description="Customer-facing display name"
    )
    value: str = Field(..., description="Internal value (system reference)")
    sort_order: int = Field(
        default=0,
        description="Sort order for consistent display"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (e.g., hex color code, size chart ID)"
    )


class VariationCreate(BaseModel):
    """
    Request model for creating a product variation (REQ-8.5)
    """
    sku: str = Field(..., description="Unique SKU for this variation")
    name: str = Field(..., description="Variation-specific product name")
    price: float = Field(..., ge=0, description="Price for this variation")
    attributes: List[VariationAttribute] = Field(
        ...,
        description="Variation attributes (color, size, etc.)"
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="Variation-specific images"
    )
    description: Optional[str] = Field(
        default=None,
        description="Additional variation-specific description"
    )
    specifications: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Variation-specific specifications (overrides parent)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Additional tags for this variation"
    )


class ParentProductCreate(BaseModel):
    """
    Request model for creating parent product with variations (REQ-8.5)
    """
    name: str = Field(..., description="Parent product name")
    description: str = Field(..., description="Parent product description")
    brand: str = Field(..., description="Brand name")
    department: Optional[str] = Field(default=None, description="Department")
    category: Optional[str] = Field(default=None, description="Category")
    subcategory: Optional[str] = Field(default=None, description="Subcategory")
    variation_theme: VariationTheme = Field(
        ...,
        description="Variation theme (e.g., 'color-size')"
    )
    base_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Base price (optional, variations have individual prices)"
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="Parent product images"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Parent product tags (inherited by children)"
    )
    specifications: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Base specifications (inherited by children)"
    )
    variations: List[VariationCreate] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Product variations (1-1000 per parent)"
    )


class VariationMatrix(BaseModel):
    """
    Variation matrix for API consumers (REQ-8.4)
    """
    sku: str = Field(..., description="Variation SKU")
    attributes: Dict[str, str] = Field(
        ...,
        description="Variation attributes (e.g., {'color': 'Black', 'size': 'M'})"
    )
    price: float = Field(..., description="Variation price")
    available: bool = Field(
        default=True,
        description="Availability status (from inventory)"
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="Variation-specific images"
    )


class ParentProductResponse(BaseModel):
    """
    Response model for parent product with variations (REQ-8.4)
    """
    parent_id: str = Field(..., description="Parent product ID")
    name: str = Field(..., description="Parent product name")
    description: str = Field(..., description="Parent product description")
    brand: str = Field(..., description="Brand name")
    department: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    variation_theme: str = Field(..., description="Variation theme")
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None
    variations: List[VariationMatrix] = Field(
        ...,
        description="All available variations"
    )
    total_variations: int = Field(
        ...,
        description="Total number of variations"
    )


class VariationUpdate(BaseModel):
    """
    Request model for updating a variation (REQ-8.5)
    """
    name: Optional[str] = Field(default=None, description="Updated name")
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Updated price"
    )
    attributes: Optional[List[VariationAttribute]] = Field(
        default=None,
        description="Updated variation attributes"
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="Updated images"
    )
    description: Optional[str] = Field(
        default=None,
        description="Updated description"
    )
    specifications: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated specifications"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Updated tags"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Active status (soft delete support)"
    )


class AddVariationRequest(BaseModel):
    """
    Request model for adding new variation to existing parent (REQ-8.5)
    """
    variation: VariationCreate = Field(
        ...,
        description="New variation to add"
    )


class VariationFilterRequest(BaseModel):
    """
    Request model for filtering variations by attributes (REQ-8.4)
    """
    attributes: Dict[str, str] = Field(
        ...,
        description="Attribute filters (e.g., {'color': 'Black', 'size': 'M'})"
    )
