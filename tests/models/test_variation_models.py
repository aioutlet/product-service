"""
Unit tests for Product Variation Models
"""

import pytest
from pydantic import ValidationError
from src.models.variation import (
    VariationType,
    InventoryMode,
    VariantAttribute,
    VariantAttributeOption,
    VariantAttributeDefinition,
    CreateVariationRequest,
    UpdateVariationRequest,
    ProductVariationSummary,
    BulkCreateVariationsRequest
)


class TestVariationType:
    """Test VariationType enum"""
    
    def test_variation_types(self):
        """Test all variation type values"""
        assert VariationType.PARENT == "parent"
        assert VariationType.CHILD == "child"
        assert VariationType.STANDALONE == "standalone"


class TestVariantAttribute:
    """Test VariantAttribute model"""
    
    def test_valid_variant_attribute(self):
        """Test creating valid variant attribute"""
        attr = VariantAttribute(name="color", value="red")
        assert attr.name == "color"
        assert attr.value == "red"
        assert attr.display_name is None
    
    def test_variant_attribute_with_display_name(self):
        """Test variant attribute with display name"""
        attr = VariantAttribute(
            name="size",
            value="xl",
            display_name="Extra Large"
        )
        assert attr.name == "size"
        assert attr.value == "xl"
        assert attr.display_name == "Extra Large"
    
    def test_attribute_name_normalization(self):
        """Test attribute name is normalized to lowercase"""
        attr = VariantAttribute(name="COLOR", value="blue")
        assert attr.name == "color"
        
        attr2 = VariantAttribute(name="  Size  ", value="M")
        assert attr2.name == "size"
    
    def test_missing_required_fields(self):
        """Test validation fails for missing required fields"""
        with pytest.raises(ValidationError):
            VariantAttribute(name="color")  # Missing value
        
        with pytest.raises(ValidationError):
            VariantAttribute(value="red")  # Missing name


class TestVariantAttributeOption:
    """Test VariantAttributeOption model"""
    
    def test_valid_option(self):
        """Test creating valid option"""
        option = VariantAttributeOption(value="red", display_name="Red")
        assert option.value == "red"
        assert option.display_name == "Red"
        assert option.is_available is True
        assert option.additional_price == 0.0
    
    def test_option_with_additional_price(self):
        """Test option with additional price"""
        option = VariantAttributeOption(
            value="premium",
            additional_price=10.00
        )
        assert option.additional_price == 10.00


class TestVariantAttributeDefinition:
    """Test VariantAttributeDefinition model"""
    
    def test_valid_definition(self):
        """Test creating valid attribute definition"""
        definition = VariantAttributeDefinition(
            name="color",
            display_name="Color",
            options=[
                VariantAttributeOption(value="red", display_name="Red"),
                VariantAttributeOption(value="blue", display_name="Blue")
            ]
        )
        assert definition.name == "color"
        assert definition.display_name == "Color"
        assert len(definition.options) == 2
        assert definition.is_required is True
        assert definition.display_order == 0


class TestCreateVariationRequest:
    """Test CreateVariationRequest model"""
    
    def test_valid_creation_request(self):
        """Test creating valid variation request"""
        request = CreateVariationRequest(
            parent_id="parent123",
            name="Test Product - Red",
            sku="TEST-RED",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        assert request.parent_id == "parent123"
        assert request.name == "Test Product - Red"
        assert request.sku == "TEST-RED"
        assert len(request.variant_attributes) == 1
        assert request.is_active is True
    
    def test_with_price_override(self):
        """Test variation with price override"""
        request = CreateVariationRequest(
            parent_id="parent123",
            name="Premium Variant",
            sku="PREMIUM",
            price=99.99,
            compare_at_price=129.99,
            variant_attributes=[
                VariantAttribute(name="tier", value="premium")
            ]
        )
        assert request.price == 99.99
        assert request.compare_at_price == 129.99
    
    def test_multiple_variant_attributes(self):
        """Test variation with multiple attributes"""
        request = CreateVariationRequest(
            parent_id="parent123",
            name="T-Shirt - Red XL",
            sku="TSHIRT-RED-XL",
            variant_attributes=[
                VariantAttribute(name="color", value="red"),
                VariantAttribute(name="size", value="xl")
            ]
        )
        assert len(request.variant_attributes) == 2
    
    def test_missing_required_fields(self):
        """Test validation fails for missing required fields"""
        with pytest.raises(ValidationError):
            CreateVariationRequest(
                name="Test",
                sku="TEST",
                variant_attributes=[]
            )  # Missing parent_id
    
    def test_empty_variant_attributes(self):
        """Test validation fails for empty variant attributes"""
        with pytest.raises(ValidationError):
            CreateVariationRequest(
                parent_id="parent123",
                name="Test",
                sku="TEST",
                variant_attributes=[]  # Should have at least 1
            )
    
    def test_invalid_price(self):
        """Test validation fails for invalid price"""
        with pytest.raises(ValidationError):
            CreateVariationRequest(
                parent_id="parent123",
                name="Test",
                sku="TEST",
                price=-10.00,  # Must be > 0
                variant_attributes=[
                    VariantAttribute(name="color", value="red")
                ]
            )


class TestUpdateVariationRequest:
    """Test UpdateVariationRequest model"""
    
    def test_valid_update_request(self):
        """Test creating valid update request"""
        request = UpdateVariationRequest(
            name="Updated Name",
            price=39.99
        )
        assert request.name == "Updated Name"
        assert request.price == 39.99
    
    def test_partial_update(self):
        """Test partial update with only some fields"""
        request = UpdateVariationRequest(is_active=False)
        assert request.is_active is False
        assert request.name is None
        assert request.price is None
    
    def test_update_variant_attributes(self):
        """Test updating variant attributes"""
        request = UpdateVariationRequest(
            variant_attributes=[
                VariantAttribute(name="color", value="blue")
            ]
        )
        assert len(request.variant_attributes) == 1
        assert request.variant_attributes[0].value == "blue"


class TestProductVariationSummary:
    """Test ProductVariationSummary model"""
    
    def test_valid_summary(self):
        """Test creating valid variation summary"""
        summary = ProductVariationSummary(
            product_id="prod123",
            product_name="Test Product",
            variation_type=VariationType.PARENT,
            child_count=5
        )
        assert summary.product_id == "prod123"
        assert summary.product_name == "Test Product"
        assert summary.variation_type == VariationType.PARENT
        assert summary.child_count == 5
    
    def test_child_variation_summary(self):
        """Test child variation summary"""
        summary = ProductVariationSummary(
            product_id="child123",
            product_name="Test Product - Red",
            variation_type=VariationType.CHILD,
            parent_id="parent123",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        assert summary.variation_type == VariationType.CHILD
        assert summary.parent_id == "parent123"
        assert len(summary.variant_attributes) == 1


class TestBulkCreateVariationsRequest:
    """Test BulkCreateVariationsRequest model"""
    
    def test_valid_bulk_request(self):
        """Test creating valid bulk request"""
        request = BulkCreateVariationsRequest(
            parent_id="parent123",
            variations=[
                CreateVariationRequest(
                    parent_id="parent123",
                    name="Variant 1",
                    sku="VAR1",
                    variant_attributes=[
                        VariantAttribute(name="color", value="red")
                    ]
                ),
                CreateVariationRequest(
                    parent_id="parent123",
                    name="Variant 2",
                    sku="VAR2",
                    variant_attributes=[
                        VariantAttribute(name="color", value="blue")
                    ]
                )
            ]
        )
        assert request.parent_id == "parent123"
        assert len(request.variations) == 2
        assert request.auto_generate_names is False
    
    def test_auto_generate_names(self):
        """Test bulk request with auto-generate names"""
        request = BulkCreateVariationsRequest(
            parent_id="parent123",
            auto_generate_names=True,
            variations=[
                CreateVariationRequest(
                    parent_id="parent123",
                    name="placeholder",
                    sku="VAR1",
                    variant_attributes=[
                        VariantAttribute(name="color", value="red")
                    ]
                )
            ]
        )
        assert request.auto_generate_names is True
    
    def test_empty_variations_list(self):
        """Test validation fails for empty variations"""
        with pytest.raises(ValidationError):
            BulkCreateVariationsRequest(
                parent_id="parent123",
                variations=[]  # Should have at least 1
            )
