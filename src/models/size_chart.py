"""
Size Chart Models

Defines data models for product size charts with support for multiple formats
(image, PDF, JSON) and regional sizing systems (US, EU, UK, Asian).
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class SizeChartFormat(str, Enum):
    """Supported size chart formats"""
    IMAGE = "image"  # PNG, JPG
    PDF = "pdf"      # PDF document
    JSON = "json"    # Structured JSON data


class RegionalSizing(str, Enum):
    """Supported regional sizing systems"""
    US = "us"
    EU = "eu"
    UK = "uk"
    ASIAN = "asian"
    INTERNATIONAL = "international"


class SizeChartEntry(BaseModel):
    """
    Single entry in a structured size chart (for JSON format).
    
    Example for clothing:
    {
        "size": "M",
        "measurements": {
            "chest": "38-40",
            "waist": "32-34",
            "hips": "40-42"
        },
        "units": "inches"
    }
    """
    size: str = Field(..., description="Size label (S, M, L, XL, 8, 10, etc.)")
    measurements: Dict[str, str] = Field(
        ...,
        description="Measurement values (chest, waist, length, etc.)"
    )
    units: str = Field(default="inches", description="Measurement units")
    regional_equivalent: Optional[Dict[RegionalSizing, str]] = Field(
        None,
        description="Equivalent sizes in other regions"
    )


class CreateSizeChartRequest(BaseModel):
    """Request model for creating a new size chart"""
    name: str = Field(..., min_length=1, max_length=200, description="Size chart name")
    category: str = Field(
        ...,
        min_length=1,
        description="Product category (Tops, Bottoms, Shoes, etc.)"
    )
    format: SizeChartFormat = Field(..., description="Chart format type")
    regional_sizing: RegionalSizing = Field(
        default=RegionalSizing.US,
        description="Primary regional sizing system"
    )
    
    # Format-specific fields
    image_url: Optional[str] = Field(None, description="URL for image format")
    pdf_url: Optional[str] = Field(None, description="URL for PDF format")
    structured_data: Optional[List[SizeChartEntry]] = Field(
        None,
        description="Structured data for JSON format"
    )
    
    # Metadata
    description: Optional[str] = Field(None, max_length=1000)
    is_template: bool = Field(
        default=False,
        description="Whether this is a reusable template"
    )
    applicable_brands: Optional[List[str]] = Field(
        None,
        description="Brands this size chart applies to"
    )
    
    @model_validator(mode='after')
    def validate_format_specific_fields(self):
        """Ensure format-specific fields are provided"""
        if self.format == SizeChartFormat.IMAGE and not self.image_url:
            raise ValueError("image_url is required when format is 'image'")
        if self.format == SizeChartFormat.PDF and not self.pdf_url:
            raise ValueError("pdf_url is required when format is 'pdf'")
        if self.format == SizeChartFormat.JSON:
            if not self.structured_data:
                raise ValueError("structured_data is required when format is 'json'")
            if len(self.structured_data) == 0:
                raise ValueError("structured_data cannot be empty")
        return self


class UpdateSizeChartRequest(BaseModel):
    """Request model for updating an existing size chart"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Format-specific updates
    image_url: Optional[str] = None
    pdf_url: Optional[str] = None
    structured_data: Optional[List[SizeChartEntry]] = None
    
    # Metadata updates
    applicable_brands: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SizeChartResponse(BaseModel):
    """Response model for size chart operations"""
    id: str = Field(..., alias="_id")
    name: str
    category: str
    format: SizeChartFormat
    regional_sizing: RegionalSizing
    
    # Format-specific fields
    image_url: Optional[str] = None
    pdf_url: Optional[str] = None
    structured_data: Optional[List[SizeChartEntry]] = None
    
    # Metadata
    description: Optional[str] = None
    is_template: bool = False
    is_active: bool = True
    applicable_brands: Optional[List[str]] = None
    usage_count: int = Field(default=0, description="Number of products using this chart")
    
    # Audit fields
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    class Config:
        populate_by_name = True


class SizeChartSummary(BaseModel):
    """Simplified size chart info for listing"""
    id: str = Field(..., alias="_id")
    name: str
    category: str
    format: SizeChartFormat
    regional_sizing: RegionalSizing
    is_template: bool
    usage_count: int
    created_at: datetime
    
    class Config:
        populate_by_name = True


class SizeChartTemplate(BaseModel):
    """Predefined size chart template"""
    template_id: str
    name: str
    category: str
    format: SizeChartFormat
    regional_sizing: RegionalSizing
    description: str
    preview_url: Optional[str] = None
