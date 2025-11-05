"""
Unit tests for attribute schema models
"""

import pytest
from pydantic import ValidationError

from src.models.attribute_schema import (
    AttributeDataType,
    AttributeUnit,
    AttributeCategory,
    ValidationRule,
    AttributeDefinition,
    AttributeGroup,
    CategorySchema,
    ProductAttributes,
    AttributeValidationError,
    AttributeValidationResult,
    FacetValue,
    Facet,
    FacetedSearchResult,
    CreateSchemaRequest,
    UpdateSchemaRequest,
    SchemaResponse
)


class TestEnums:
    """Test enum definitions"""
    
    def test_attribute_data_type_values(self):
        """Test AttributeDataType enum has correct values"""
        assert AttributeDataType.STRING == "string"
        assert AttributeDataType.NUMBER == "number"
        assert AttributeDataType.BOOLEAN == "boolean"
        assert AttributeDataType.LIST == "list"
        assert AttributeDataType.OBJECT == "object"
        assert AttributeDataType.ENUM == "enum"
    
    def test_attribute_unit_values(self):
        """Test AttributeUnit enum has common units"""
        assert AttributeUnit.INCHES == "inches"
        assert AttributeUnit.CENTIMETERS == "cm"
        assert AttributeUnit.POUNDS == "lbs"
        assert AttributeUnit.KILOGRAMS == "kg"
        assert AttributeUnit.LITERS == "L"
        assert AttributeUnit.WATTS == "W"
    
    def test_attribute_category_values(self):
        """Test AttributeCategory enum"""
        assert AttributeCategory.PHYSICAL_DIMENSIONS == "physical_dimensions"
        assert AttributeCategory.MATERIALS_COMPOSITION == "materials_composition"
        assert AttributeCategory.CARE_INSTRUCTIONS == "care_instructions"


class TestValidationRule:
    """Test ValidationRule model"""
    
    def test_create_validation_rule(self):
        """Test creating a validation rule"""
        rule = ValidationRule(
            rule_type="min",
            value=5,
            error_message="Value must be at least 5"
        )
        assert rule.rule_type == "min"
        assert rule.value == 5
        assert rule.error_message == "Value must be at least 5"
    
    def test_validation_rule_optional_message(self):
        """Test validation rule without error message"""
        rule = ValidationRule(rule_type="required", value=True)
        assert rule.rule_type == "required"
        assert rule.error_message is None


class TestAttributeDefinition:
    """Test AttributeDefinition model"""
    
    def test_create_basic_attribute(self):
        """Test creating a basic attribute definition"""
        attr = AttributeDefinition(
            name="length",
            display_name="Length",
            data_type=AttributeDataType.NUMBER,
            unit=AttributeUnit.INCHES
        )
        assert attr.name == "length"
        assert attr.display_name == "Length"
        assert attr.data_type == AttributeDataType.NUMBER
        assert attr.unit == AttributeUnit.INCHES
        assert attr.required is False
    
    def test_create_required_attribute(self):
        """Test creating a required attribute"""
        attr = AttributeDefinition(
            name="fit_type",
            display_name="Fit Type",
            data_type=AttributeDataType.ENUM,
            required=True,
            allowed_values=["Regular", "Slim", "Relaxed"]
        )
        assert attr.required is True
        assert attr.allowed_values == ["Regular", "Slim", "Relaxed"]
    
    def test_attribute_with_validation_rules(self):
        """Test attribute with validation rules"""
        attr = AttributeDefinition(
            name="weight",
            display_name="Weight",
            data_type=AttributeDataType.NUMBER,
            unit=AttributeUnit.POUNDS,
            validation_rules=[
                ValidationRule(rule_type="min", value=0),
                ValidationRule(rule_type="max", value=1000)
            ]
        )
        assert len(attr.validation_rules) == 2
        assert attr.validation_rules[0].rule_type == "min"
    
    def test_attribute_with_default_value(self):
        """Test attribute with default value"""
        attr = AttributeDefinition(
            name="eco_friendly",
            display_name="Eco Friendly",
            data_type=AttributeDataType.BOOLEAN,
            default_value=False
        )
        assert attr.default_value is False
    
    def test_attribute_with_regex_pattern(self):
        """Test attribute with regex pattern"""
        attr = AttributeDefinition(
            name="model_number",
            display_name="Model Number",
            data_type=AttributeDataType.STRING,
            regex_pattern=r"^[A-Z]{2}\d{4}$"
        )
        assert attr.regex_pattern == r"^[A-Z]{2}\d{4}$"


class TestAttributeGroup:
    """Test AttributeGroup model"""
    
    def test_create_attribute_group(self):
        """Test creating an attribute group"""
        group = AttributeGroup(
            name="dimensions",
            display_name="Physical Dimensions",
            category=AttributeCategory.PHYSICAL_DIMENSIONS,
            attributes=[
                AttributeDefinition(
                    name="length",
                    display_name="Length",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.INCHES
                )
            ]
        )
        assert group.name == "dimensions"
        assert len(group.attributes) == 1
        assert group.order == 0
    
    def test_attribute_group_with_order(self):
        """Test attribute group with custom order"""
        group = AttributeGroup(
            name="materials",
            display_name="Materials",
            category=AttributeCategory.MATERIALS_COMPOSITION,
            attributes=[],
            order=2
        )
        assert group.order == 2


class TestCategorySchema:
    """Test CategorySchema model"""
    
    def test_create_category_schema(self):
        """Test creating a category schema"""
        schema = CategorySchema(
            category_name="Clothing",
            display_name="Clothing & Apparel",
            attribute_groups=[
                AttributeGroup(
                    name="dimensions",
                    display_name="Dimensions",
                    category=AttributeCategory.PHYSICAL_DIMENSIONS,
                    attributes=[]
                )
            ]
        )
        assert schema.category_name == "Clothing"
        assert schema.version == "1.0"
        assert schema.is_active is True
        assert len(schema.attribute_groups) == 1
    
    def test_category_schema_versioning(self):
        """Test schema versioning"""
        schema = CategorySchema(
            category_name="Electronics",
            display_name="Electronics",
            attribute_groups=[],
            version="2.0"
        )
        assert schema.version == "2.0"


class TestProductAttributes:
    """Test ProductAttributes model"""
    
    def test_create_empty_attributes(self):
        """Test creating empty product attributes"""
        attrs = ProductAttributes()
        assert attrs.physical_dimensions is None
        assert attrs.materials_composition is None
        assert attrs.care_instructions is None
    
    def test_create_attributes_with_data(self):
        """Test creating product attributes with data"""
        attrs = ProductAttributes(
            physical_dimensions={"length": 10, "width": 5},
            materials_composition={"primary_material": "Cotton"},
            category_specific={"fit_type": "Regular"}
        )
        assert attrs.physical_dimensions["length"] == 10
        assert attrs.materials_composition["primary_material"] == "Cotton"
        assert attrs.category_specific["fit_type"] == "Regular"


class TestValidationModels:
    """Test validation result models"""
    
    def test_create_validation_error(self):
        """Test creating a validation error"""
        error = AttributeValidationError(
            attribute_name="length",
            attribute_path="physical_dimensions.length",
            error_code="INVALID_TYPE",
            error_message="Expected number, got string",
            expected_type="number",
            actual_value="ten"
        )
        assert error.attribute_name == "length"
        assert error.error_code == "INVALID_TYPE"
        assert error.expected_type == "number"
    
    def test_validation_error_with_constraint(self):
        """Test validation error with constraint"""
        error = AttributeValidationError(
            attribute_name="weight",
            attribute_path="physical_dimensions.weight",
            error_code="OUT_OF_RANGE",
            error_message="Value must be between 0 and 1000",
            constraint="Value must be between 0 and 1000"
        )
        assert error.constraint == "Value must be between 0 and 1000"
    
    def test_create_validation_result_success(self):
        """Test creating a successful validation result"""
        result = AttributeValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_attributes={"length": 10}
        )
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_create_validation_result_with_errors(self):
        """Test creating validation result with errors"""
        result = AttributeValidationResult(
            is_valid=False,
            errors=[
                AttributeValidationError(
                    attribute_name="length",
                    attribute_path="physical_dimensions.length",
                    error_code="REQUIRED",
                    error_message="Length is required"
                )
            ],
            warnings=[]
        )
        assert result.is_valid is False
        assert len(result.errors) == 1


class TestSearchModels:
    """Test faceted search models"""
    
    def test_create_facet_value(self):
        """Test creating a facet value"""
        value = FacetValue(
            value="Regular",
            count=25,
            display_name="Regular Fit"
        )
        assert value.value == "Regular"
        assert value.count == 25
        assert value.display_name == "Regular Fit"
    
    def test_create_facet(self):
        """Test creating a facet"""
        facet = Facet(
            attribute_name="fit_type",
            display_name="Fit Type",
            values=[
                FacetValue(value="Regular", count=25),
                FacetValue(value="Slim", count=15)
            ]
        )
        assert facet.attribute_name == "fit_type"
        assert len(facet.values) == 2
        assert facet.selected_values == []
    
    def test_facet_with_selected_values(self):
        """Test facet with selected values"""
        facet = Facet(
            attribute_name="fit_type",
            display_name="Fit Type",
            values=[FacetValue(value="Regular", count=25)],
            selected_values=["Regular"]
        )
        assert facet.selected_values == ["Regular"]
    
    def test_create_faceted_search_result(self):
        """Test creating faceted search result"""
        result = FacetedSearchResult(
            products=[{"id": "1", "name": "Product 1"}],
            facets=[
                Facet(
                    attribute_name="fit_type",
                    display_name="Fit Type",
                    values=[FacetValue(value="Regular", count=25)]
                )
            ],
            total_count=100,
            applied_filters={"fit_type": ["Regular"]},
            page=1,
            page_size=20
        )
        assert len(result.products) == 1
        assert len(result.facets) == 1
        assert result.total_count == 100
        assert result.page == 1


class TestSchemaRequestModels:
    """Test schema request/response models"""
    
    def test_create_schema_request(self):
        """Test creating a schema creation request"""
        request = CreateSchemaRequest(
            category_name="Test Category",
            display_name="Test Category Display",
            attribute_groups=[
                AttributeGroup(
                    name="test",
                    display_name="Test",
                    category=AttributeCategory.CATEGORY_SPECIFIC,
                    attributes=[]
                )
            ]
        )
        assert request.category_name == "Test Category"
        assert len(request.attribute_groups) == 1
    
    def test_update_schema_request(self):
        """Test creating a schema update request"""
        request = UpdateSchemaRequest(
            display_name="Updated Display Name",
            is_active=False
        )
        assert request.display_name == "Updated Display Name"
        assert request.is_active is False
    
    def test_update_schema_request_partial(self):
        """Test partial schema update"""
        request = UpdateSchemaRequest()
        assert request.display_name is None
        assert request.attribute_groups is None
    
    def test_schema_response(self):
        """Test schema response model"""
        response = SchemaResponse(
            id="507f1f77bcf86cd799439011",
            category_name="Clothing",
            display_name="Clothing & Apparel",
            attribute_groups=[],
            version="1.0",
            is_active=True,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert response.category_name == "Clothing"
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.created_at == "2024-01-01T00:00:00Z"
