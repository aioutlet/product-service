"""
Unit tests for image handler service.
"""

import pytest
import zipfile
from io import BytesIO

from src.services.image_handler_service import ImageHandlerService


class TestImageHandlerService:
    """Test image handler service."""
    
    @pytest.fixture
    def service(self):
        """Create image handler service."""
        return ImageHandlerService()
    
    @pytest.fixture
    def sample_products(self):
        """Create sample products for testing."""
        return [
            {"sku": "PROD-001", "name": "Product 1"},
            {"sku": "PROD-002", "name": "Product 2"},
            {"sku": "TEST-123", "name": "Test Product"}
        ]
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.MAX_IMAGE_SIZE == 10 * 1024 * 1024
        assert service.MAX_IMAGES_PER_PRODUCT == 10
    
    def test_allowed_formats(self, service):
        """Test allowed image formats."""
        assert "jpg" in service.ALLOWED_FORMATS
        assert "jpeg" in service.ALLOWED_FORMATS
        assert "png" in service.ALLOWED_FORMATS
        assert "webp" in service.ALLOWED_FORMATS
    
    # Image URL Validation Tests
    
    def test_validate_valid_http_url(self, service):
        """Test validating valid HTTP URL."""
        result = service.validate_image_url("http://example.com/image.jpg")
        
        assert result.is_valid is True
        assert result.error_message is None
        assert result.url == "http://example.com/image.jpg"
    
    def test_validate_valid_https_url(self, service):
        """Test validating valid HTTPS URL."""
        result = service.validate_image_url("https://cdn.example.com/products/image.png")
        
        assert result.is_valid is True
        assert result.error_message is None
    
    def test_validate_url_with_port(self, service):
        """Test validating URL with port number."""
        result = service.validate_image_url("http://localhost:8080/image.jpg")
        
        assert result.is_valid is True
    
    def test_validate_url_with_query_params(self, service):
        """Test validating URL with query parameters."""
        result = service.validate_image_url("https://example.com/image.jpg?size=large&quality=high")
        
        assert result.is_valid is True
    
    def test_validate_empty_url(self, service):
        """Test validating empty URL."""
        result = service.validate_image_url("")
        
        assert result.is_valid is False
        assert "empty" in result.error_message.lower()
    
    def test_validate_whitespace_url(self, service):
        """Test validating whitespace-only URL."""
        result = service.validate_image_url("   ")
        
        assert result.is_valid is False
    
    def test_validate_invalid_protocol(self, service):
        """Test validating URL with invalid protocol."""
        result = service.validate_image_url("ftp://example.com/image.jpg")
        
        assert result.is_valid is False
        assert "http" in result.error_message.lower()
    
    def test_validate_invalid_extension(self, service):
        """Test validating URL with invalid extension."""
        result = service.validate_image_url("https://example.com/image.gif")
        
        assert result.is_valid is False
        assert "format" in result.error_message.lower()
    
    def test_validate_no_extension(self, service):
        """Test validating URL without extension."""
        result = service.validate_image_url("https://example.com/image")
        
        assert result.is_valid is False
    
    def test_validate_jpeg_extension(self, service):
        """Test validating JPEG extension."""
        result = service.validate_image_url("https://example.com/image.jpeg")
        
        assert result.is_valid is True
    
    def test_validate_webp_extension(self, service):
        """Test validating WebP extension."""
        result = service.validate_image_url("https://cdn.example.com/products/image.webp")
        
        assert result.is_valid is True
    
    # ZIP File Processing Tests
    
    def create_test_zip(self, files):
        """Helper to create a test ZIP file."""
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files.items():
                zip_file.writestr(filename, content)
        return zip_buffer.getvalue()
    
    def test_process_zip_with_matching_images(self, service, sample_products):
        """Test processing ZIP with images matching SKUs."""
        # Create ZIP with matching images
        files = {
            "PROD-001-1.jpg": b"fake image data",
            "PROD-002-1.png": b"fake image data",
            "TEST-123-primary.jpg": b"fake image data"
        }
        zip_content = self.create_test_zip(files)
        
        result = service.process_zip_upload(zip_content, sample_products)
        
        assert "PROD-001" in result
        assert "PROD-002" in result
        assert "TEST-123" in result
        assert len(result["PROD-001"]) > 0
    
    def test_process_zip_with_multiple_images_per_sku(self, service, sample_products):
        """Test processing ZIP with multiple images per SKU."""
        files = {
            "PROD-001-1.jpg": b"fake image data",
            "PROD-001-2.jpg": b"fake image data",
            "PROD-001-3.png": b"fake image data"
        }
        zip_content = self.create_test_zip(files)
        
        result = service.process_zip_upload(zip_content, sample_products)
        
        assert len(result["PROD-001"]) == 3
    
    def test_process_zip_skips_hidden_files(self, service, sample_products):
        """Test ZIP processing skips hidden files."""
        files = {
            ".DS_Store": b"mac metadata",
            "PROD-001-1.jpg": b"fake image data",
            ".hidden/PROD-002-1.jpg": b"fake image data"
        }
        zip_content = self.create_test_zip(files)
        
        result = service.process_zip_upload(zip_content, sample_products)
        
        # Should only process PROD-001
        assert len(result["PROD-001"]) > 0
    
    def test_process_zip_with_directories(self, service, sample_products):
        """Test ZIP processing handles directory structure."""
        files = {
            "images/": b"",  # Directory entry
            "images/PROD-001-1.jpg": b"fake image data",
            "products/PROD-002-1.png": b"fake image data"
        }
        zip_content = self.create_test_zip(files)
        
        result = service.process_zip_upload(zip_content, sample_products)
        
        assert "PROD-001" in result
        assert "PROD-002" in result
    
    def test_process_zip_enforces_max_images(self, service, sample_products):
        """Test ZIP processing enforces max images per product."""
        # Create 15 images for one SKU (exceeds limit of 10)
        files = {
            f"PROD-001-{i}.jpg": b"fake image data"
            for i in range(1, 16)
        }
        zip_content = self.create_test_zip(files)
        
        result = service.process_zip_upload(zip_content, sample_products)
        
        # Should only store max 10 images
        assert len(result["PROD-001"]) <= service.MAX_IMAGES_PER_PRODUCT
    
    def test_process_zip_skips_unmatched_images(self, service, sample_products):
        """Test ZIP processing skips images that don't match any SKU."""
        files = {
            "PROD-001-1.jpg": b"fake image data",
            "UNKNOWN-SKU-1.jpg": b"fake image data",
            "random-image.png": b"fake image data"
        }
        zip_content = self.create_test_zip(files)
        
        result = service.process_zip_upload(zip_content, sample_products)
        
        # Should only match PROD-001
        assert len(result["PROD-001"]) > 0
        assert "UNKNOWN-SKU" not in result
    
    def test_process_invalid_zip(self, service, sample_products):
        """Test processing invalid ZIP file."""
        invalid_zip = b"not a zip file"
        
        with pytest.raises(ValueError) as exc_info:
            service.process_zip_upload(invalid_zip, sample_products)
        
        assert "zip" in str(exc_info.value).lower()
    
    # Image Matching Tests
    
    def test_match_image_with_sequence_number(self, service, sample_products):
        """Test matching image with sequence number pattern."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("PROD-001-1.jpg", sku_to_product)
        
        assert result is not None
        assert result[0] == "PROD-001"
        assert result[1] == "PROD-001-1.jpg"
    
    def test_match_image_with_label(self, service, sample_products):
        """Test matching image with label pattern."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("PROD-001-primary.png", sku_to_product)
        
        assert result is not None
        assert result[0] == "PROD-001"
    
    def test_match_image_without_suffix(self, service, sample_products):
        """Test matching image without suffix (SKU only)."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("PROD-001.jpg", sku_to_product)
        
        assert result is not None
        assert result[0] == "PROD-001"
    
    def test_match_image_case_insensitive(self, service, sample_products):
        """Test matching is case-insensitive."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("prod-001-1.jpg", sku_to_product)
        
        assert result is not None
        assert result[0] == "PROD-001"
    
    def test_match_image_invalid_extension(self, service, sample_products):
        """Test matching rejects invalid extensions."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("PROD-001-1.gif", sku_to_product)
        
        assert result is None
    
    def test_match_image_no_extension(self, service, sample_products):
        """Test matching rejects files without extension."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("PROD-001-1", sku_to_product)
        
        assert result is None
    
    def test_match_image_unknown_sku(self, service, sample_products):
        """Test matching returns None for unknown SKU."""
        sku_to_product = {p["sku"]: p for p in sample_products}
        
        result = service._match_image_to_sku("UNKNOWN-999-1.jpg", sku_to_product)
        
        assert result is None
    
    # Merge Images Tests
    
    def test_merge_images_with_products(self, service, sample_products):
        """Test merging images with products."""
        sku_images = {
            "PROD-001": ["image1.jpg", "image2.png"],
            "PROD-002": ["image1.jpg"],
            "TEST-123": []
        }
        
        result = service.merge_images_with_products(
            sample_products,
            sku_images
        )
        
        assert result[0]["images"] == ["image1.jpg", "image2.png"]
        assert result[1]["images"] == ["image1.jpg"]
        assert "images" not in result[2] or result[2].get("images") == []
    
    def test_merge_images_no_matches(self, service, sample_products):
        """Test merging when no images match."""
        sku_images = {
            "PROD-001": [],
            "PROD-002": [],
            "TEST-123": []
        }
        
        result = service.merge_images_with_products(
            sample_products,
            sku_images
        )
        
        # Products should not have images field
        for product in result:
            assert "images" not in product or product.get("images") == []
