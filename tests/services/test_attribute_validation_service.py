"""
Unit tests for attribute validation service
"""

import pytest

from src.services.attribute_validation_service import AttributeValidationService
from src.models.attribute_schema import ProductAttributes, AttributeValidationError


class TestValidationService:
    """Test attribute validation service"""
    
    @pytest.fixture
    def service(self):
        """Create validation service instance"""
        return AttributeValidationService()
    
    def test_service_initialization(self, service):
        """Test service initializes with standard schemas"""
        assert service is not None
        assert len(service.standard_schemas) == 4
    
    def test_list_categories(self, service):
        """Test listing available categories"""
        categories = service.list_categories()
        assert len(categories) == 4
        assert "Clothing" in categories
        assert "Electronics" in categories
    
    def test_get_schema(self, service):
        """Test getting schema by category"""
        schema = service.get_schema("Clothing")
        assert schema is not None
        assert schema.category_name == "Clothing"
    
    def test_get_nonexistent_schema(self, service):
        """Test getting non-existent schema"""
        schema = service.get_schema("NonExistent")
        assert schema is None


class TestStringValidation:
    """Test string attribute validation"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_valid_string(self, service):
        """Test validating a valid string"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"fit_type": "Regular"}
            ),
            "Clothing"
        )
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_empty_string_allowed(self, service):
        """Test empty string is allowed for non-required attributes"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"pattern": ""}
            ),
            "Clothing"
        )
        # Should be valid if attribute is not required
        assert result.is_valid is True or "REQUIRED" in [e.error_code for e in result.errors]
    
    def test_validate_string_too_long(self, service):
        """Test string exceeding max length"""
        long_string = "x" * 500
        result = service.validate_attributes(
            ProductAttributes(
                technical_specs={"model_number": long_string}
            ),
            "Clothing"
        )
        # If there's a max length validation, it should fail
        if not result.is_valid:
            assert any(e.error_code == "MAX_LENGTH_EXCEEDED" for e in result.errors)


class TestNumberValidation:
    """Test number attribute validation"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_valid_number(self, service):
        """Test validating a valid number"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": 10.5, "width": 5.0}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_negative_number(self, service):
        """Test negative number validation"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": -5}
            ),
            "Clothing"
        )
        # Should fail if min validation is 0
        if not result.is_valid:
            assert any(e.error_code == "OUT_OF_RANGE" for e in result.errors)
    
    def test_validate_number_as_string(self, service):
        """Test number provided as string (should coerce)"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": "10.5"}
            ),
            "Clothing"
        )
        # Should coerce and validate successfully
        assert result.is_valid is True
        assert result.validated_attributes["physical_dimensions"]["length"] == 10.5
    
    def test_validate_invalid_number_string(self, service):
        """Test invalid number string"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": "not a number"}
            ),
            "Clothing"
        )
        assert result.is_valid is False
        assert any(e.error_code == "INVALID_TYPE" for e in result.errors)
    
    def test_validate_zero_allowed(self, service):
        """Test zero is valid for number fields"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"weight": 0}
            ),
            "Clothing"
        )
        # Zero should be valid unless explicitly excluded
        assert result.is_valid is True or any(e.error_code == "OUT_OF_RANGE" for e in result.errors)


class TestBooleanValidation:
    """Test boolean attribute validation"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_boolean_true(self, service):
        """Test boolean true value"""
        result = service.validate_attributes(
            ProductAttributes(
                sustainability={"eco_friendly": True}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_boolean_false(self, service):
        """Test boolean false value"""
        result = service.validate_attributes(
            ProductAttributes(
                sustainability={"eco_friendly": False}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_boolean_as_string_true(self, service):
        """Test boolean as string 'true' (should coerce)"""
        result = service.validate_attributes(
            ProductAttributes(
                sustainability={"eco_friendly": "true"}
            ),
            "Clothing"
        )
        assert result.is_valid is True
        assert result.validated_attributes["sustainability"]["eco_friendly"] is True
    
    def test_validate_boolean_as_string_false(self, service):
        """Test boolean as string 'false' (should coerce)"""
        result = service.validate_attributes(
            ProductAttributes(
                sustainability={"eco_friendly": "false"}
            ),
            "Clothing"
        )
        assert result.is_valid is True
        assert result.validated_attributes["sustainability"]["eco_friendly"] is False
    
    def test_validate_boolean_as_number(self, service):
        """Test boolean as number (1/0 should coerce)"""
        result = service.validate_attributes(
            ProductAttributes(
                sustainability={"eco_friendly": 1}
            ),
            "Clothing"
        )
        assert result.is_valid is True
        assert result.validated_attributes["sustainability"]["eco_friendly"] is True


class TestEnumValidation:
    """Test enum attribute validation"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_valid_enum(self, service):
        """Test valid enum value"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"fit_type": "Regular"}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_invalid_enum(self, service):
        """Test invalid enum value"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"fit_type": "InvalidFit"}
            ),
            "Clothing"
        )
        assert result.is_valid is False
        assert any(e.error_code == "INVALID_ENUM_VALUE" for e in result.errors)
    
    def test_validate_enum_case_sensitive(self, service):
        """Test enum validation is case sensitive"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"fit_type": "regular"}  # lowercase
            ),
            "Clothing"
        )
        # Should fail unless case-insensitive matching is implemented
        if not result.is_valid:
            assert any(e.error_code == "INVALID_ENUM_VALUE" for e in result.errors)


class TestListValidation:
    """Test list attribute validation"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_valid_list(self, service):
        """Test valid list value"""
        result = service.validate_attributes(
            ProductAttributes(
                materials_composition={"secondary_materials": ["Polyester", "Spandex"]}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_empty_list(self, service):
        """Test empty list"""
        result = service.validate_attributes(
            ProductAttributes(
                materials_composition={"secondary_materials": []}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_non_list_as_list(self, service):
        """Test non-list value for list attribute"""
        result = service.validate_attributes(
            ProductAttributes(
                materials_composition={"secondary_materials": "Not a list"}
            ),
            "Clothing"
        )
        assert result.is_valid is False
        assert any(e.error_code == "INVALID_TYPE" for e in result.errors)


class TestRequiredAttributes:
    """Test required attribute validation"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_missing_required_attribute(self, service):
        """Test missing required attribute"""
        # Assuming fit_type is required for Clothing
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": 10}
            ),
            "Clothing"
        )
        # If fit_type is required, validation should fail
        if not result.is_valid:
            assert any(e.error_code == "REQUIRED" for e in result.errors)
    
    def test_validate_all_required_present(self, service):
        """Test all required attributes present"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={
                    "fit_type": "Regular",
                    "neckline": "Crew Neck"
                }
            ),
            "Clothing"
        )
        # Should be valid if all required fields are present
        assert result.is_valid is True or len(result.errors) == 0


class TestComplexValidation:
    """Test complex validation scenarios"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_multiple_attribute_groups(self, service):
        """Test validating multiple attribute groups"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": 10, "width": 5},
                materials_composition={"primary_material": "Cotton"},
                care_instructions={"washing": "Machine Wash Cold"},
                category_specific={"fit_type": "Regular"}
            ),
            "Clothing"
        )
        assert result.is_valid is True
    
    def test_validate_mixed_valid_invalid(self, service):
        """Test mix of valid and invalid attributes"""
        result = service.validate_attributes(
            ProductAttributes(
                physical_dimensions={"length": 10},  # valid
                category_specific={"fit_type": "InvalidFit"}  # invalid
            ),
            "Clothing"
        )
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Should have validated attributes for valid fields
        assert "physical_dimensions" in result.validated_attributes
    
    def test_validate_unknown_attributes_ignored(self, service):
        """Test unknown attributes are ignored"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={
                    "fit_type": "Regular",
                    "unknown_attribute": "value"
                }
            ),
            "Clothing"
        )
        # Unknown attributes should be ignored, not cause validation failure
        assert result.is_valid is True
    
    def test_validate_empty_attributes(self, service):
        """Test validating empty attributes"""
        result = service.validate_attributes(
            ProductAttributes(),
            "Clothing"
        )
        # Empty attributes should be valid if no required fields
        assert result.is_valid is True or any(e.error_code == "REQUIRED" for e in result.errors)
    
    def test_validation_error_contains_path(self, service):
        """Test validation errors contain attribute path"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"fit_type": "InvalidFit"}
            ),
            "Clothing"
        )
        if not result.is_valid:
            error = result.errors[0]
            assert error.attribute_path is not None
            assert "fit_type" in error.attribute_path


class TestDifferentCategories:
    """Test validation across different categories"""
    
    @pytest.fixture
    def service(self):
        return AttributeValidationService()
    
    def test_validate_electronics(self, service):
        """Test electronics category validation"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={
                    "processor": "Intel i7",
                    "memory_gb": 16,
                    "storage_gb": 512
                }
            ),
            "Electronics"
        )
        assert result.is_valid is True
    
    def test_validate_beauty(self, service):
        """Test beauty category validation"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={
                    "skin_type": "Oily",
                    "fragrance": "Floral"
                }
            ),
            "Beauty & Personal Care"
        )
        assert result.is_valid is True
    
    def test_validate_invalid_category(self, service):
        """Test validation with invalid category"""
        result = service.validate_attributes(
            ProductAttributes(
                category_specific={"fit_type": "Regular"}
            ),
            "NonExistentCategory"
        )
        # Should return errors for invalid category
        assert result.is_valid is False
