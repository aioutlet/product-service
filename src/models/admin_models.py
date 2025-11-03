"""
Admin Models
Data models for admin-specific features.
Implements PRD REQ-5.4 (Size Charts) and REQ-5.5 (Restrictions)
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# REQ-5.4: Size Chart Management
# ============================================================================

class SizeChartDimension(BaseModel):
    """Single measurement dimension in a size chart"""
    size: str  # e.g., "S", "M", "L", "XL"
    measurements: Dict[str, str]  # e.g., {"chest": "36-38", "waist": "30-32"}


class SizeChart(BaseModel):
    """
    Size chart for product categories.
    Supports multiple formats and regional sizing.
    """
    id: Optional[str] = None
    name: str  # e.g., "Men's T-Shirt Size Chart"
    category: str  # e.g., "Clothing > Men > Tops"
    format_type: str  # "structured", "image", "pdf"
    
    # For structured format
    dimensions: List[SizeChartDimension] = []
    measurement_unit: str = "inches"  # "inches", "cm"
    region: str = "US"  # "US", "EU", "UK", "Asian"
    
    # For image/PDF format
    image_url: Optional[str] = None
    pdf_url: Optional[str] = None
    
    # Metadata
    version: int = 1
    is_template: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Men's T-Shirt Size Chart",
                "category": "Clothing > Men > Tops",
                "format_type": "structured",
                "dimensions": [
                    {
                        "size": "S",
                        "measurements": {
                            "chest": "34-36",
                            "length": "28",
                            "shoulder": "17"
                        }
                    },
                    {
                        "size": "M",
                        "measurements": {
                            "chest": "38-40",
                            "length": "29",
                            "shoulder": "18"
                        }
                    }
                ],
                "measurement_unit": "inches",
                "region": "US"
            }
        }


# ============================================================================
# REQ-5.5: Product Restrictions & Compliance
# ============================================================================

class AgeRestriction(BaseModel):
    """Age restriction configuration"""
    type: str  # "none", "18+", "21+", "custom"
    minimum_age: Optional[int] = None
    description: Optional[str] = None


class ShippingRestriction(BaseModel):
    """Shipping restriction configuration"""
    hazmat: bool = False
    oversized: bool = False
    perishable: bool = False
    international_restricted: bool = False
    regional_restricted: bool = False
    ground_only: bool = False
    restrictions_description: Optional[str] = None


class RegionalAvailability(BaseModel):
    """Regional availability configuration"""
    available_countries: List[str] = []  # ISO country codes
    available_states: List[str] = []  # State/province codes
    restricted_countries: List[str] = []
    restricted_states: List[str] = []


class ComplianceMetadata(BaseModel):
    """Compliance and certification metadata"""
    certifications: List[str] = []  # e.g., ["CE", "FCC", "UL"]
    safety_warnings: List[str] = []
    ingredient_disclosure: Optional[str] = None
    country_of_origin: Optional[str] = None
    warranty_info: Optional[str] = None
    material_composition: Optional[str] = None


class ProductRestrictions(BaseModel):
    """
    Complete product restrictions and compliance data.
    Implements REQ-5.5: Product Restrictions & Compliance
    """
    age_restriction: AgeRestriction = Field(
        default_factory=lambda: AgeRestriction(type="none")
    )
    shipping_restrictions: ShippingRestriction = Field(
        default_factory=ShippingRestriction
    )
    regional_availability: RegionalAvailability = Field(
        default_factory=RegionalAvailability
    )
    compliance_metadata: ComplianceMetadata = Field(
        default_factory=ComplianceMetadata
    )


# ============================================================================
# REQ-5.2: Bulk Import Models
# ============================================================================

class BulkImportJob(BaseModel):
    """Bulk import job status tracking"""
    job_id: str
    filename: str
    status: str  # "pending", "processing", "completed", "failed", "cancelled"
    total_rows: int
    processed_rows: int = 0
    success_count: int = 0
    error_count: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    created_by: str
    error_report_url: Optional[str] = None
    import_mode: str = "partial"  # "partial" or "all-or-nothing"


class ImportValidationError(BaseModel):
    """Single validation error in bulk import"""
    row_number: int
    field_name: str
    error_description: str
    suggested_correction: Optional[str] = None
    current_value: Optional[str] = None
