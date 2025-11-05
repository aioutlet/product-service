"""
Product Restrictions and Compliance Models

Handles age restrictions, shipping restrictions, regional availability,
and compliance metadata for products.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AgeRestriction(str, Enum):
    """Age restriction levels"""
    NONE = "none"
    EIGHTEEN_PLUS = "18+"
    TWENTY_ONE_PLUS = "21+"
    CUSTOM = "custom"


class ShippingRestrictionType(str, Enum):
    """Types of shipping restrictions"""
    HAZMAT = "hazmat"
    OVERSIZED = "oversized"
    PERISHABLE = "perishable"
    INTERNATIONAL_RESTRICTED = "international_restricted"
    REGIONAL_RESTRICTED = "regional_restricted"
    GROUND_ONLY = "ground_only"
    FRAGILE = "fragile"
    TEMPERATURE_CONTROLLED = "temperature_controlled"


class ShippingRestriction(BaseModel):
    """Shipping restriction details"""
    type: ShippingRestrictionType
    reason: Optional[str] = Field(None, description="Reason for restriction")
    additional_info: Optional[str] = Field(None, description="Additional information or instructions")
    
    class Config:
        use_enum_values = True


class RegionalAvailability(BaseModel):
    """Regional availability configuration"""
    available_countries: Optional[List[str]] = Field(
        None,
        description="ISO 3166-1 alpha-2 country codes where product is available"
    )
    restricted_countries: Optional[List[str]] = Field(
        None,
        description="ISO 3166-1 alpha-2 country codes where product is NOT available"
    )
    available_states: Optional[Dict[str, List[str]]] = Field(
        None,
        description="States/provinces by country code where product is available"
    )
    restricted_states: Optional[Dict[str, List[str]]] = Field(
        None,
        description="States/provinces by country code where product is NOT available"
    )
    available_regions: Optional[List[str]] = Field(
        None,
        description="Custom regions where product is available"
    )
    
    @field_validator('available_countries', 'restricted_countries')
    @classmethod
    def validate_country_codes(cls, v):
        """Validate country codes are 2-letter ISO codes"""
        if v:
            for code in v:
                if not (isinstance(code, str) and len(code) == 2 and code.isupper()):
                    raise ValueError(f"Invalid country code: {code}. Must be 2-letter uppercase ISO 3166-1 alpha-2 code")
        return v


class ComplianceCertification(BaseModel):
    """Product certification details"""
    name: str = Field(..., description="Certification name (e.g., 'FDA Approved', 'CE Mark')")
    authority: Optional[str] = Field(None, description="Certifying authority")
    certification_number: Optional[str] = Field(None, description="Certification/license number")
    issued_date: Optional[datetime] = Field(None, description="Date certification was issued")
    expiry_date: Optional[datetime] = Field(None, description="Date certification expires")
    document_url: Optional[str] = Field(None, description="URL to certification document")


class SafetyWarning(BaseModel):
    """Product safety warning"""
    type: str = Field(..., description="Warning type (e.g., 'choking_hazard', 'flammable')")
    message: str = Field(..., description="Warning message to display")
    severity: str = Field(
        default="medium",
        description="Severity level: low, medium, high, critical"
    )
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """Validate severity level"""
        valid_levels = ['low', 'medium', 'high', 'critical']
        if v not in valid_levels:
            raise ValueError(f"Severity must be one of: {', '.join(valid_levels)}")
        return v


class IngredientDisclosure(BaseModel):
    """Ingredient or material disclosure"""
    name: str = Field(..., description="Ingredient/material name")
    percentage: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Percentage of total composition"
    )
    cas_number: Optional[str] = Field(None, description="CAS Registry Number")
    allergen: bool = Field(default=False, description="Whether this is a known allergen")
    organic: bool = Field(default=False, description="Whether this is organic certified")


class WarrantyInfo(BaseModel):
    """Product warranty information"""
    duration_months: int = Field(..., ge=0, description="Warranty duration in months")
    type: str = Field(..., description="Warranty type (e.g., 'manufacturer', 'extended', 'lifetime')")
    coverage: str = Field(..., description="What the warranty covers")
    provider: Optional[str] = Field(None, description="Warranty provider name")
    terms_url: Optional[str] = Field(None, description="URL to warranty terms and conditions")
    transferable: bool = Field(default=False, description="Whether warranty can be transferred")


class ComplianceMetadata(BaseModel):
    """Compliance and regulatory metadata"""
    certifications: Optional[List[ComplianceCertification]] = Field(
        None,
        description="Product certifications and licenses"
    )
    safety_warnings: Optional[List[SafetyWarning]] = Field(
        None,
        description="Safety warnings to display"
    )
    ingredients: Optional[List[IngredientDisclosure]] = Field(
        None,
        description="Ingredient or material disclosures"
    )
    country_of_origin: Optional[str] = Field(
        None,
        description="ISO 3166-1 alpha-2 country code for origin"
    )
    manufactured_date: Optional[datetime] = Field(
        None,
        description="Date product was manufactured"
    )
    warranty: Optional[WarrantyInfo] = Field(
        None,
        description="Warranty information"
    )
    regulatory_codes: Optional[Dict[str, str]] = Field(
        None,
        description="Regulatory codes by authority (e.g., {'FDA': 'NDC-12345', 'EPA': 'REG-67890'})"
    )
    disposal_instructions: Optional[str] = Field(
        None,
        description="Product disposal instructions"
    )
    recycling_info: Optional[str] = Field(
        None,
        description="Recycling information"
    )
    
    @field_validator('country_of_origin')
    @classmethod
    def validate_country_of_origin(cls, v):
        """Validate country of origin is 2-letter ISO code"""
        if v and not (isinstance(v, str) and len(v) == 2 and v.isupper()):
            raise ValueError("Country of origin must be 2-letter uppercase ISO 3166-1 alpha-2 code")
        return v


class ProductRestrictions(BaseModel):
    """Complete product restrictions configuration"""
    age_restriction: AgeRestriction = Field(
        default=AgeRestriction.NONE,
        description="Age restriction level"
    )
    custom_age_limit: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Custom age limit (required if age_restriction is 'custom')"
    )
    shipping_restrictions: Optional[List[ShippingRestriction]] = Field(
        None,
        description="Shipping restrictions"
    )
    regional_availability: Optional[RegionalAvailability] = Field(
        None,
        description="Regional availability configuration"
    )
    compliance: Optional[ComplianceMetadata] = Field(
        None,
        description="Compliance and regulatory metadata"
    )
    prescription_required: bool = Field(
        default=False,
        description="Whether product requires a prescription"
    )
    license_required: bool = Field(
        default=False,
        description="Whether product requires a license to purchase"
    )
    
    @field_validator('custom_age_limit')
    @classmethod
    def validate_custom_age(cls, v, info):
        """Validate custom age limit is provided when age_restriction is custom"""
        if info.data.get('age_restriction') == AgeRestriction.CUSTOM and v is None:
            raise ValueError("custom_age_limit is required when age_restriction is 'custom'")
        return v
    
    class Config:
        use_enum_values = True


class UpdateProductRestrictionsRequest(BaseModel):
    """Request to update product restrictions"""
    restrictions: ProductRestrictions = Field(..., description="Updated restrictions")


class ProductRestrictionsResponse(BaseModel):
    """Response containing product restrictions"""
    product_id: str
    sku: str
    restrictions: ProductRestrictions
    updated_at: datetime
    updated_by: Optional[str] = None
