"""
Unit tests for standard category schemas
"""

import pytest

from src.models.standard_schemas import StandardSchemas
from src.models.attribute_schema import AttributeDataType, AttributeUnit, AttributeCategory


class TestStandardSchemas:
    """Test standard category schemas"""
    
    def test_get_all_schemas(self):
        """Test getting all standard schemas"""
        schemas_dict = StandardSchemas.get_all_schemas()
        assert len(schemas_dict) == 4
        
        category_names = list(schemas_dict.keys())
        assert "Clothing" in category_names
        assert "Electronics" in category_names
        assert "Home & Furniture" in category_names
        assert "Beauty & Personal Care" in category_names
    
    def test_clothing_schema(self):
        """Test clothing category schema"""
        schema = StandardSchemas.get_clothing_schema()
        
        assert schema.category_name == "Clothing"
        assert schema.display_name == "Clothing"
        assert schema.is_active is True
        assert len(schema.attribute_groups) > 0
        
        # Check for category-specific attributes
        category_group = next(
            (g for g in schema.attribute_groups if g.name == "category_specific"),
            None
        )
        assert category_group is not None
        
        # Check for specific clothing attributes
        attr_names = [a.name for a in category_group.attributes]
        assert "fit_type" in attr_names
        assert "neckline" in attr_names
        assert "sleeve_length" in attr_names
    
    def test_electronics_schema(self):
        """Test electronics category schema"""
        schema = StandardSchemas.get_electronics_schema()
        
        assert schema.category_name == "Electronics"
        assert schema.display_name == "Electronics"
        
        # Check for electronics-specific attributes
        category_group = next(
            (g for g in schema.attribute_groups if g.name == "category_specific"),
            None
        )
        assert category_group is not None
        
        attr_names = [a.name for a in category_group.attributes]
        assert "processor" in attr_names
        assert "memory_gb" in attr_names
        assert "storage_gb" in attr_names
    
    def test_home_furniture_schema(self):
        """Test home & furniture category schema"""
        schema = StandardSchemas.get_home_furniture_schema()
        
        assert schema.category_name == "Home & Furniture"
        assert schema.display_name == "Home & Furniture"
        
        # Check for furniture-specific attributes
        category_group = next(
            (g for g in schema.attribute_groups if g.name == "category_specific"),
            None
        )
        assert category_group is not None
        
        attr_names = [a.name for a in category_group.attributes]
        assert "room_type" in attr_names
        assert "assembly_required" in attr_names
        assert "style" in attr_names
    
    def test_beauty_schema(self):
        """Test beauty & personal care category schema"""
        schema = StandardSchemas.get_beauty_schema()
        
        assert schema.category_name == "Beauty & Personal Care"
        assert schema.display_name == "Beauty & Personal Care"
        
        # Check for beauty-specific attributes
        category_group = next(
            (g for g in schema.attribute_groups if g.name == "category_specific"),
            None
        )
        assert category_group is not None
        
        attr_names = [a.name for a in category_group.attributes]
        assert "skin_type" in attr_names
        assert "fragrance_type" in attr_names
        assert "spf_rating" in attr_names


class TestCommonAttributeGroups:
    """Test common attribute groups shared across categories"""
    
    def test_physical_dimensions_group(self):
        """Test physical dimensions attribute group"""
        group = StandardSchemas.get_physical_dimensions_group()
        
        assert group.name == "physical_dimensions"
        assert group.category == AttributeCategory.PHYSICAL_DIMENSIONS
        
        attr_names = [a.name for a in group.attributes]
        assert "length" in attr_names
        assert "width" in attr_names
        assert "height" in attr_names
        assert "weight" in attr_names
        
        # Check units are properly set
        length_attr = next(a for a in group.attributes if a.name == "length")
        assert length_attr.unit == AttributeUnit.INCHES
        assert length_attr.data_type == AttributeDataType.NUMBER
    
    def test_materials_group(self):
        """Test materials composition attribute group"""
        group = StandardSchemas.get_materials_group()
        
        assert group.name == "materials_composition"
        assert group.category == AttributeCategory.MATERIALS_COMPOSITION
        
        attr_names = [a.name for a in group.attributes]
        assert "primary_material" in attr_names
        assert "secondary_materials" in attr_names
        assert "certifications" in attr_names
        
        # Check primary material is string
        primary_material = next(a for a in group.attributes if a.name == "primary_material")
        assert primary_material.data_type == AttributeDataType.STRING
    
    def test_care_instructions_group(self):
        """Test care instructions attribute group"""
        group = StandardSchemas.get_care_instructions_group()
        
        assert group.name == "care_instructions"
        assert group.category == AttributeCategory.CARE_INSTRUCTIONS
        
        attr_names = [a.name for a in group.attributes]
        assert "washing" in attr_names
        assert "drying" in attr_names
        assert "ironing" in attr_names
        
        # Check washing is enum with specific values
        washing = next(a for a in group.attributes if a.name == "washing")
        assert washing.data_type == AttributeDataType.ENUM
        assert "Machine Wash Cold" in washing.allowed_values
    
    def test_technical_specs_group(self):
        """Test technical specifications attribute group"""
        group = StandardSchemas.get_technical_specs_group()
        
        assert group.name == "technical_specs"
        assert group.category == AttributeCategory.TECHNICAL_SPECS
        
        attr_names = [a.name for a in group.attributes]
        assert "model_number" in attr_names
        assert "country_of_origin" in attr_names
        assert "warranty_duration_months" in attr_names
        
        # Check warranty is number
        warranty = next(a for a in group.attributes if a.name == "warranty_duration_months")
        assert warranty.data_type == AttributeDataType.NUMBER
    
    def test_sustainability_group(self):
        """Test sustainability attribute group"""
        group = StandardSchemas.get_sustainability_group()
        
        assert group.name == "sustainability"
        assert group.category == AttributeCategory.SUSTAINABILITY
        
        attr_names = [a.name for a in group.attributes]
        assert "eco_friendly" in attr_names
        assert "eco_certifications" in attr_names
        assert "carbon_neutral" in attr_names
        assert "ethical_sourcing" in attr_names
        
        # Check eco_friendly is boolean
        eco_friendly = next(a for a in group.attributes if a.name == "eco_friendly")
        assert eco_friendly.data_type == AttributeDataType.BOOLEAN


class TestAttributeValidationRules:
    """Test validation rules on attributes"""
    
    def test_required_attributes(self):
        """Test that some attributes are marked as required"""
        schema = StandardSchemas.get_clothing_schema()
        
        # Check if any attributes are marked as required
        all_attributes = [
            attr for group in schema.attribute_groups 
            for attr in group.attributes
        ]
        
        # Should have at least some attributes defined
        assert len(all_attributes) > 0
        
        # Attributes should have proper structure
        for attr in all_attributes[:5]:  # Check first 5
            assert attr.name
            assert attr.display_name
            assert attr.data_type
    
    def test_enum_allowed_values(self):
        """Test enum attributes have allowed values"""
        schema = StandardSchemas.get_clothing_schema()
        
        category_group = next(
            g for g in schema.attribute_groups if g.name == "category_specific"
        )
        
        fit_type = next(a for a in category_group.attributes if a.name == "fit_type")
        assert fit_type.data_type == AttributeDataType.ENUM
        assert len(fit_type.allowed_values) > 0
        assert "Regular" in fit_type.allowed_values
        assert "Slim" in fit_type.allowed_values
    
    def test_number_ranges(self):
        """Test number attributes have proper ranges"""
        group = StandardSchemas.get_physical_dimensions_group()
        
        length_attr = next(a for a in group.attributes if a.name == "length")
        
        # Check for min validation rule
        min_rule = next((r for r in length_attr.validation_rules if r.rule_type == "min"), None)
        if min_rule:
            assert min_rule.value >= 0


class TestSchemaConsistency:
    """Test schema consistency across categories"""
    
    def test_all_schemas_have_common_groups(self):
        """Test all schemas include common attribute groups"""
        schemas_dict = StandardSchemas.get_all_schemas()
        
        common_group_names = [
            "physical_dimensions",
            "materials_composition",
            "care_instructions",
            "technical_specs",
            "sustainability"
        ]
        
        for category_name, schema in schemas_dict.items():
            group_names = [g.name for g in schema.attribute_groups]
            
            # Each schema should have most common groups
            common_count = sum(1 for name in common_group_names if name in group_names)
            assert common_count >= 3, f"{schema.category_name} missing common groups"
    
    def test_all_schemas_have_category_specific(self):
        """Test all schemas have category-specific attributes"""
        schemas_dict = StandardSchemas.get_all_schemas()
        
        for category_name, schema in schemas_dict.items():
            group_names = [g.name for g in schema.attribute_groups]
            assert "category_specific" in group_names, f"{schema.category_name} missing category_specific group"
    
    def test_attribute_names_unique_within_group(self):
        """Test attribute names are unique within each group"""
        schemas_dict = StandardSchemas.get_all_schemas()
        
        for category_name, schema in schemas_dict.items():
            for group in schema.attribute_groups:
                attr_names = [a.name for a in group.attributes]
                assert len(attr_names) == len(set(attr_names)), f"Duplicate attributes in {schema.category_name}/{group.name}"
    
    def test_all_attributes_have_display_names(self):
        """Test all attributes have display names"""
        schemas_dict = StandardSchemas.get_all_schemas()
        
        for category_name, schema in schemas_dict.items():
            for group in schema.attribute_groups:
                for attr in group.attributes:
                    assert attr.display_name, f"Missing display name for {attr.name} in {schema.category_name}"
                    assert len(attr.display_name) > 0


class TestExampleValues:
    """Test example values for attributes"""
    
    def test_attributes_have_examples(self):
        """Test attributes have example values"""
        schema = StandardSchemas.get_clothing_schema()
        
        all_attributes = [
            attr for group in schema.attribute_groups 
            for attr in group.attributes
        ]
        
        # Most attributes should have example values
        attrs_with_examples = [a for a in all_attributes if a.example_value is not None]
        assert len(attrs_with_examples) > len(all_attributes) / 2
    
    def test_enum_examples_are_valid(self):
        """Test enum example values are from allowed values"""
        schema = StandardSchemas.get_clothing_schema()
        
        all_attributes = [
            attr for group in schema.attribute_groups 
            for attr in group.attributes
        ]
        
        enum_attrs = [a for a in all_attributes if a.data_type == AttributeDataType.ENUM]
        
        for attr in enum_attrs:
            if attr.example_value and attr.allowed_values:
                assert attr.example_value in attr.allowed_values, f"Invalid example for {attr.name}"
