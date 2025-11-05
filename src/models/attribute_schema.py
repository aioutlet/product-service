"""
Product Attribute Schema Models

Defines structured schemas for product attributes with validation rules.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class AttributeDataType(str, Enum):
    """Supported attribute data types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"  # Array of strings
    OBJECT = "object"  # Nested object
    ENUM = "enum"  # Fixed set of values


class AttributeUnit(str, Enum):
    """Common measurement units"""
    # Length
    INCHES = "inches"
    CENTIMETERS = "cm"
    METERS = "m"
    FEET = "ft"
    
    # Weight
    POUNDS = "lbs"
    KILOGRAMS = "kg"
    GRAMS = "g"
    OUNCES = "oz"
    
    # Volume
    LITERS = "L"
    MILLILITERS = "ml"
    GALLONS = "gal"
    FLUID_OUNCES = "fl_oz"
    
    # Other
    PERCENTAGE = "%"
    WATTS = "W"
    VOLTS = "V"
    HERTZ = "Hz"
    PIXELS = "px"


class ValidationRule(BaseModel):
    """Validation rule for an attribute"""
    rule_type: str = Field(..., description="Type of validation (min, max, regex, length, etc.)")
    value: Any = Field(..., description="Rule value")
    error_message: Optional[str] = Field(None, description="Custom error message")


class AttributeDefinition(BaseModel):
    """
    Definition of a single attribute.
    
    Example:
    {
        "name": "length",
        "display_name": "Length",
        "data_type": "number",
        "unit": "inches",
        "required": true,
        "default_value": null,
        "allowed_values": null,
        "min_value": 0,
        "max_value": 1000,
        "description": "Product length in inches"
    }
    """
    name: str = Field(..., description="Attribute key name (e.g., 'length', 'color')")
    display_name: str = Field(..., description="Human-readable display name")
    data_type: AttributeDataType = Field(..., description="Data type of the attribute")
    unit: Optional[AttributeUnit] = Field(None, description="Measurement unit if applicable")
    required: bool = Field(default=False, description="Whether attribute is required")
    default_value: Optional[Any] = Field(None, description="Default value if not provided")
    allowed_values: Optional[List[str]] = Field(None, description="List of allowed values for enum type")
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum value for numbers")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum value for numbers")
    min_length: Optional[int] = Field(None, description="Minimum length for strings/lists")
    max_length: Optional[int] = Field(None, description="Maximum length for strings/lists")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern for string validation")
    description: Optional[str] = Field(None, description="Description of the attribute")
    example_value: Optional[Any] = Field(None, description="Example value")
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="Additional validation rules")
    
    @validator('allowed_values')
    def validate_allowed_values(cls, v, values):
        """Validate that allowed_values is only set for enum type"""
        if v is not None and values.get('data_type') != AttributeDataType.ENUM:
            raise ValueError("allowed_values can only be set for enum data type")
        return v
    
    @validator('unit')
    def validate_unit(cls, v, values):
        """Validate that unit is only set for number type"""
        if v is not None and values.get('data_type') != AttributeDataType.NUMBER:
            raise ValueError("unit can only be set for number data type")
        return v


class AttributeCategory(str, Enum):
    """Standard attribute categories"""
    PHYSICAL_DIMENSIONS = "physical_dimensions"
    MATERIALS_COMPOSITION = "materials_composition"
    CARE_INSTRUCTIONS = "care_instructions"
    PRODUCT_FEATURES = "product_features"
    TECHNICAL_SPECS = "technical_specs"
    SUSTAINABILITY = "sustainability"
    CATEGORY_SPECIFIC = "category_specific"


class AttributeGroup(BaseModel):
    """
    Group of related attributes.
    
    Example: Physical Dimensions group contains length, width, height, weight
    """
    name: str = Field(..., description="Group name")
    display_name: str = Field(..., description="Display name for UI")
    category: AttributeCategory = Field(..., description="Attribute category")
    description: Optional[str] = Field(None, description="Group description")
    attributes: List[AttributeDefinition] = Field(..., description="Attributes in this group")
    order: int = Field(default=0, description="Display order")


class CategorySchema(BaseModel):
    """
    Complete attribute schema for a product category.
    
    Example: Clothing category has groups for dimensions, materials, care, etc.
    """
    category_name: str = Field(..., description="Product category name (e.g., 'Clothing')")
    display_name: str = Field(..., description="Display name for UI")
    description: Optional[str] = Field(None, description="Category description")
    attribute_groups: List[AttributeGroup] = Field(..., description="Attribute groups for this category")
    version: str = Field(default="1.0", description="Schema version")
    is_active: bool = Field(default=True, description="Whether schema is active")
    
    class Config:
        use_enum_values = True


class ProductAttributes(BaseModel):
    """
    Product attributes organized by category.
    
    Example:
    {
        "physical_dimensions": {
            "length": 24.0,
            "width": 18.0,
            "height": 2.0,
            "weight": 5.5,
            "length_unit": "inches",
            "weight_unit": "lbs"
        },
        "materials_composition": {
            "primary_material": "Cotton",
            "material_percentages": {
                "cotton": 95,
                "spandex": 5
            },
            "certifications": ["GOTS Certified Organic"]
        },
        "category_specific": {
            "fit_type": "Regular",
            "neckline": "Crew",
            "sleeve_length": "Short"
        }
    }
    """
    physical_dimensions: Optional[Dict[str, Any]] = Field(None, description="Physical dimensions")
    materials_composition: Optional[Dict[str, Any]] = Field(None, description="Materials and composition")
    care_instructions: Optional[Dict[str, Any]] = Field(None, description="Care instructions")
    product_features: Optional[Dict[str, Any]] = Field(None, description="Product features")
    technical_specs: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")
    sustainability: Optional[Dict[str, Any]] = Field(None, description="Sustainability information")
    category_specific: Optional[Dict[str, Any]] = Field(None, description="Category-specific attributes")
    
    def get_all_attributes(self) -> Dict[str, Any]:
        """Get all attributes as a flat dictionary"""
        result = {}
        for category, attrs in self.dict(exclude_none=True).items():
            if attrs:
                result[category] = attrs
        return result


class AttributeValidationError(BaseModel):
    """Validation error for an attribute"""
    attribute_name: str = Field(..., description="Name of the attribute with error")
    attribute_path: str = Field(..., description="Full path to attribute (e.g., 'physical_dimensions.length')")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    expected_type: Optional[str] = Field(None, description="Expected data type")
    actual_value: Optional[Any] = Field(None, description="Actual value provided")
    allowed_values: Optional[List[str]] = Field(None, description="Allowed values for enum")
    constraint: Optional[str] = Field(None, description="Constraint that was violated")


class AttributeValidationResult(BaseModel):
    """Result of attribute validation"""
    is_valid: bool = Field(..., description="Whether attributes are valid")
    errors: List[AttributeValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    validated_attributes: Optional[Dict[str, Any]] = Field(None, description="Validated and normalized attributes")


class FacetValue(BaseModel):
    """A single value in a facet with count"""
    value: str = Field(..., description="Facet value")
    count: int = Field(..., description="Number of products with this value")
    display_name: Optional[str] = Field(None, description="Display name for UI")


class Facet(BaseModel):
    """A facet for filtering with available values"""
    attribute_name: str = Field(..., description="Attribute name")
    display_name: str = Field(..., description="Display name for UI")
    values: List[FacetValue] = Field(..., description="Available values with counts")
    selected_values: List[str] = Field(default_factory=list, description="Currently selected values")


class FacetedSearchResult(BaseModel):
    """Result of faceted search with products and facets"""
    products: List[Dict[str, Any]] = Field(..., description="Matching products")
    facets: List[Facet] = Field(..., description="Available facets for filtering")
    total_count: int = Field(..., description="Total number of matching products")
    applied_filters: Dict[str, List[str]] = Field(default_factory=dict, description="Currently applied filters")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Items per page")


# Schema Request/Response Models

class CreateSchemaRequest(BaseModel):
    """Request to create a new category schema"""
    category_name: str
    display_name: str
    description: Optional[str] = None
    attribute_groups: List[AttributeGroup]


class UpdateSchemaRequest(BaseModel):
    """Request to update a category schema"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    attribute_groups: Optional[List[AttributeGroup]] = None
    is_active: Optional[bool] = None


class SchemaResponse(CategorySchema):
    """Response containing category schema with metadata"""
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SchemaListResponse(BaseModel):
    """Response containing list of schemas"""
    schemas: List[CategorySchema]
    total: int
