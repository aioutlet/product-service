"""
Tests for size chart models

Tests for Pydantic models including validation, enum values,
and format-specific requirements.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.size_chart import (
    SizeChartFormat,
    RegionalSizing,
    SizeChartEntry,
    CreateSizeChartRequest,
    UpdateSizeChartRequest,
    SizeChartResponse,
    SizeChartSummary,
    SizeChartTemplate
)


class TestSizeChartEnums:
    """Test size chart enums"""
    
    def test_size_chart_format_values(self):
        """Test SizeChartFormat enum has expected values"""
        assert SizeChartFormat.IMAGE.value == "image"
        assert SizeChartFormat.PDF.value == "pdf"
        assert SizeChartFormat.JSON.value == "json"
    
    def test_regional_sizing_values(self):
        """Test RegionalSizing enum has expected values"""
        assert RegionalSizing.US.value == "us"
        assert RegionalSizing.EU.value == "eu"
        assert RegionalSizing.UK.value == "uk"
        assert RegionalSizing.ASIAN.value == "asian"
        assert RegionalSizing.INTERNATIONAL.value == "international"


class TestSizeChartEntry:
    """Test SizeChartEntry model"""
    
    def test_create_valid_entry(self):
        """Test creating valid size chart entry"""
        entry = SizeChartEntry(
            size="M",
            measurements={"chest": "38-40", "waist": "32-34", "hips": "40-42"}
        )
        assert entry.size == "M"
        assert entry.measurements["chest"] == "38-40"
        assert entry.measurements["waist"] == "32-34"
        assert entry.measurements["hips"] == "40-42"
        assert entry.units == "inches"
        assert entry.regional_equivalent is None
    
    def test_entry_with_regional_equivalents(self):
        """Test entry with regional size equivalents"""
        entry = SizeChartEntry(
            size="M",
            measurements={"chest": "38-40", "waist": "32-34"},
            regional_equivalent={
                RegionalSizing.US: "M",
                RegionalSizing.EU: "48-50",
                RegionalSizing.UK: "38-40"
            }
        )
        assert entry.regional_equivalent[RegionalSizing.US] == "M"
        assert entry.regional_equivalent[RegionalSizing.EU] == "48-50"
        assert entry.regional_equivalent[RegionalSizing.UK] == "38-40"


class TestCreateSizeChartRequest:
    """Test CreateSizeChartRequest model and validation"""
    
    def test_create_image_format_chart(self):
        """Test creating image format chart"""
        request = CreateSizeChartRequest(
            name="Men's Shirt Sizes",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png"
        )
        assert request.format == SizeChartFormat.IMAGE
        assert request.image_url == "https://example.com/chart.png"
        assert request.pdf_url is None
        assert request.structured_data is None
    
    def test_create_pdf_format_chart(self):
        """Test creating PDF format chart"""
        request = CreateSizeChartRequest(
            name="Women's Dress Sizes",
            category="Clothing",
            format=SizeChartFormat.PDF,
            regional_sizing=RegionalSizing.EU,
            pdf_url="https://example.com/chart.pdf"
        )
        assert request.format == SizeChartFormat.PDF
        assert request.pdf_url == "https://example.com/chart.pdf"
    
    def test_create_json_format_chart(self):
        """Test creating JSON format chart"""
        entries = [
            SizeChartEntry(size="S", measurements={"chest": "34-36", "waist": "28-30"}),
            SizeChartEntry(size="M", measurements={"chest": "38-40", "waist": "32-34"})
        ]
        request = CreateSizeChartRequest(
            name="Standard Sizes",
            category="Clothing",
            format=SizeChartFormat.JSON,
            regional_sizing=RegionalSizing.US,
            structured_data=entries
        )
        assert request.format == SizeChartFormat.JSON
        assert len(request.structured_data) == 2
        assert request.structured_data[0].size == "S"
    
    def test_image_format_requires_image_url(self):
        """Test that IMAGE format requires image_url"""
        with pytest.raises(ValidationError) as exc_info:
            CreateSizeChartRequest(
                name="Test Chart",
                category="Clothing",
                format=SizeChartFormat.IMAGE,
                regional_sizing=RegionalSizing.US
            )
        assert "image_url is required" in str(exc_info.value)
    
    def test_pdf_format_requires_pdf_url(self):
        """Test that PDF format requires pdf_url"""
        with pytest.raises(ValidationError) as exc_info:
            CreateSizeChartRequest(
                name="Test Chart",
                category="Clothing",
                format=SizeChartFormat.PDF,
                regional_sizing=RegionalSizing.US
            )
        assert "pdf_url is required" in str(exc_info.value)
    
    def test_json_format_requires_structured_data(self):
        """Test that JSON format requires structured_data"""
        with pytest.raises(ValidationError) as exc_info:
            CreateSizeChartRequest(
                name="Test Chart",
                category="Clothing",
                format=SizeChartFormat.JSON,
                regional_sizing=RegionalSizing.US
            )
        assert "structured_data is required" in str(exc_info.value)
    
    def test_template_flag(self):
        """Test is_template flag"""
        request = CreateSizeChartRequest(
            name="Template Chart",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/template.png",
            is_template=True
        )
        assert request.is_template is True
    
    def test_applicable_brands(self):
        """Test applicable_brands field"""
        request = CreateSizeChartRequest(
            name="Brand Chart",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png",
            applicable_brands=["Nike", "Adidas"]
        )
        assert request.applicable_brands == ["Nike", "Adidas"]
    
    def test_description_field(self):
        """Test optional description field"""
        request = CreateSizeChartRequest(
            name="Test Chart",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png",
            description="Size chart for men's casual shirts"
        )
        assert request.description == "Size chart for men's casual shirts"


class TestUpdateSizeChartRequest:
    """Test UpdateSizeChartRequest model"""
    
    def test_all_fields_optional(self):
        """Test that all fields are optional"""
        request = UpdateSizeChartRequest()
        assert request.name is None
        assert request.category is None
        assert request.description is None
        assert request.image_url is None
        assert request.pdf_url is None
        assert request.structured_data is None
        assert request.applicable_brands is None
        assert request.is_active is None
    
    def test_update_name_only(self):
        """Test updating only name"""
        request = UpdateSizeChartRequest(name="New Name")
        assert request.name == "New Name"
        assert request.category is None
    
    def test_update_structured_data(self):
        """Test updating structured data"""
        entries = [SizeChartEntry(size="L", measurements={"chest": "42-44", "waist": "36-38"})]
        request = UpdateSizeChartRequest(structured_data=entries)
        assert len(request.structured_data) == 1
        assert request.structured_data[0].size == "L"
    
    def test_update_is_active(self):
        """Test updating is_active flag"""
        request = UpdateSizeChartRequest(is_active=False)
        assert request.is_active is False


class TestSizeChartResponse:
    """Test SizeChartResponse model"""
    
    def test_create_response_image_format(self):
        """Test creating response for image format"""
        response = SizeChartResponse(
            id="123",
            name="Test Chart",
            category="Clothing",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.US,
            image_url="https://example.com/chart.png",
            is_template=False,
            is_active=True,
            usage_count=5,
            created_by="user1",
            updated_by="user1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert response.id == "123"
        assert response.format == SizeChartFormat.IMAGE
        assert response.usage_count == 5
    
    def test_response_with_structured_data(self):
        """Test response with structured data"""
        response = SizeChartResponse(
            id="456",
            name="JSON Chart",
            category="Clothing",
            format=SizeChartFormat.JSON,
            regional_sizing=RegionalSizing.EU,
            structured_data=[
                SizeChartEntry(size="S", measurements={"chest": "86-91", "waist": "71-76"})
            ],
            is_template=False,
            is_active=True,
            usage_count=0,
            created_by="user1",
            updated_by="user1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert response.structured_data is not None
        assert len(response.structured_data) == 1


class TestSizeChartSummary:
    """Test SizeChartSummary model"""
    
    def test_create_summary(self):
        """Test creating size chart summary"""
        summary = SizeChartSummary(
            id="789",
            name="Summary Chart",
            category="Footwear",
            format=SizeChartFormat.IMAGE,
            regional_sizing=RegionalSizing.UK,
            is_template=True,
            usage_count=10,
            created_at=datetime.now()
        )
        assert summary.id == "789"
        assert summary.category == "Footwear"
        assert summary.is_template is True
        assert summary.usage_count == 10


class TestSizeChartTemplate:
    """Test SizeChartTemplate model"""
    
    def test_create_template(self):
        """Test creating size chart template"""
        template = SizeChartTemplate(
            template_id="template1",
            name="Standard Template",
            category="Clothing",
            format=SizeChartFormat.JSON,
            regional_sizing=RegionalSizing.US,
            description="Standard clothing sizes"
        )
        assert template.template_id == "template1"
        assert template.name == "Standard Template"
        assert template.format == SizeChartFormat.JSON
