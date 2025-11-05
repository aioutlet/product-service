"""
Image Handler Service for Bulk Import

Handles image URL validation and ZIP file processing for bulk imports.
"""

import re
import zipfile
import io
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from src.models.bulk_import import ImageUploadMethod, ImageValidationResult
from src.core.logger import logger


class ImageHandlerService:
    """
    Handles image validation and processing for bulk imports.
    
    Supports:
    - Image URL validation (format, accessibility)
    - ZIP file processing (extract, match SKUs)
    - Image format validation (JPEG, PNG, WebP)
    - Size validation (max 10MB per image)
    """
    
    # Allowed image formats
    ALLOWED_FORMATS = ['jpg', 'jpeg', 'png', 'webp']
    
    # Max image size (10MB)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    
    # Max images per product
    MAX_IMAGES_PER_PRODUCT = 10
    
    # Image URL regex pattern
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',  # path
        re.IGNORECASE
    )
    
    def validate_image_url(
        self,
        url: str,
        correlation_id: Optional[str] = None
    ) -> ImageValidationResult:
        """
        Validate an image URL.
        
        Checks:
        - URL format is valid
        - Extension is allowed (.jpg, .jpeg, .png, .webp)
        - URL is accessible (optionally)
        
        Args:
            url: Image URL to validate
            correlation_id: For logging
            
        Returns:
            ImageValidationResult with is_valid and error_message
        """
        # Check if URL is empty
        if not url or not url.strip():
            return ImageValidationResult(
                is_valid=False,
                error_message="Image URL cannot be empty"
            )
        
        url = url.strip()
        
        # Validate URL format
        if not self.URL_PATTERN.match(url):
            return ImageValidationResult(
                is_valid=False,
                error_message="Invalid URL format. Must start with http:// or https://"
            )
        
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check file extension
        has_valid_extension = any(path.endswith(f'.{ext}') for ext in self.ALLOWED_FORMATS)
        
        if not has_valid_extension:
            return ImageValidationResult(
                is_valid=False,
                error_message=f"Invalid image format. Allowed: {', '.join(self.ALLOWED_FORMATS)}"
            )
        
        logger.debug(
            f"Image URL validated successfully: {url}",
            correlation_id=correlation_id
        )
        
        return ImageValidationResult(
            is_valid=True,
            error_message=None,
            url=url
        )
    
    def process_zip_upload(
        self,
        zip_content: bytes,
        products: List[Dict],
        correlation_id: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Process ZIP file containing product images.
        
        Expected ZIP structure:
        - {SKU}-1.jpg
        - {SKU}-2.png
        - {SKU}-primary.webp
        - etc.
        
        Filename pattern: {SKU}-{sequence}.{extension}
        or: {SKU}-{label}.{extension}
        
        Args:
            zip_content: ZIP file bytes
            products: List of products to match images to
            correlation_id: For logging
            
        Returns:
            Dict mapping SKU to list of image URLs/paths
            
        Raises:
            ValueError: If ZIP is invalid or contains invalid images
        """
        logger.info(
            f"Processing ZIP file with {len(products)} products",
            correlation_id=correlation_id
        )
        
        # Extract SKUs from products
        sku_to_product = {p.get('sku'): p for p in products if p.get('sku')}
        
        # Result dictionary
        sku_images: Dict[str, List[str]] = {sku: [] for sku in sku_to_product.keys()}
        
        try:
            # Open ZIP file
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                # Get list of files
                file_list = zip_file.namelist()
                
                logger.info(
                    f"ZIP contains {len(file_list)} files",
                    correlation_id=correlation_id
                )
                
                # Process each file
                for filename in file_list:
                    # Skip directories
                    if filename.endswith('/'):
                        continue
                    
                    # Skip hidden files
                    if filename.startswith('.') or '/' + '.' in filename:
                        logger.debug(f"Skipping hidden file: {filename}")
                        continue
                    
                    # Extract basename (remove directory path)
                    basename = filename.split('/')[-1]
                    
                    # Match filename pattern: {SKU}-{sequence}.{ext}
                    match_result = self._match_image_to_sku(basename, sku_to_product)
                    
                    if not match_result:
                        logger.warning(
                            f"Could not match image to SKU: {filename}",
                            correlation_id=correlation_id
                        )
                        continue
                    
                    sku, image_name = match_result
                    
                    # Validate image
                    try:
                        image_data = zip_file.read(filename)
                        
                        # Check size
                        if len(image_data) > self.MAX_IMAGE_SIZE:
                            logger.warning(
                                f"Image {filename} exceeds max size ({len(image_data)} bytes)",
                                correlation_id=correlation_id
                            )
                            continue
                        
                        # Check count
                        if len(sku_images[sku]) >= self.MAX_IMAGES_PER_PRODUCT:
                            logger.warning(
                                f"SKU {sku} already has {self.MAX_IMAGES_PER_PRODUCT} images",
                                correlation_id=correlation_id
                            )
                            continue
                        
                        # Add to results (in production, upload to storage and get URL)
                        sku_images[sku].append(image_name)
                        
                        logger.debug(
                            f"Matched image {image_name} to SKU {sku}",
                            correlation_id=correlation_id
                        )
                    
                    except Exception as e:
                        logger.error(
                            f"Failed to process image {filename}: {str(e)}",
                            correlation_id=correlation_id
                        )
                        continue
                
                logger.info(
                    f"Processed {sum(len(imgs) for imgs in sku_images.values())} images for {len([s for s in sku_images.values() if s])} SKUs",
                    correlation_id=correlation_id
                )
                
                return sku_images
        
        except zipfile.BadZipFile:
            logger.error("Invalid ZIP file", correlation_id=correlation_id)
            raise ValueError("Invalid ZIP file format")
        
        except Exception as e:
            logger.error(
                f"Failed to process ZIP file: {str(e)}",
                correlation_id=correlation_id
            )
            raise ValueError(f"Failed to process ZIP file: {str(e)}")
    
    def _match_image_to_sku(
        self,
        filename: str,
        sku_to_product: Dict[str, Dict]
    ) -> Optional[Tuple[str, str]]:
        """
        Match image filename to product SKU.
        
        Patterns:
        - {SKU}-1.jpg → SKU, sequence number
        - {SKU}-primary.png → SKU, label
        - {SKU}.webp → SKU only
        
        Args:
            filename: Image filename
            sku_to_product: Dict mapping SKU to product
            
        Returns:
            Tuple of (SKU, image_name) if matched, None otherwise
        """
        # Remove extension
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) != 2:
            return None
        
        name_without_ext = name_parts[0]
        extension = name_parts[1].lower()
        
        # Check if extension is allowed
        if extension not in self.ALLOWED_FORMATS:
            return None
        
        # Try to match SKU patterns
        # Pattern 1: {SKU}-{sequence/label}
        if '-' in name_without_ext:
            parts = name_without_ext.split('-', 1)
            potential_sku = parts[0]
            
            if potential_sku in sku_to_product:
                return (potential_sku, filename)
        
        # Pattern 2: {SKU} only
        if name_without_ext in sku_to_product:
            return (name_without_ext, filename)
        
        # Pattern 3: Case-insensitive match
        for sku in sku_to_product.keys():
            if name_without_ext.lower().startswith(sku.lower()):
                return (sku, filename)
        
        return None
    
    def merge_images_with_products(
        self,
        products: List[Dict],
        sku_images: Dict[str, List[str]],
        correlation_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Merge image URLs/paths with product data.
        
        Adds 'images' field to each product with matched images.
        
        Args:
            products: List of product dictionaries
            sku_images: Dict mapping SKU to image URLs
            correlation_id: For logging
            
        Returns:
            Updated list of products with images field
        """
        logger.info(
            f"Merging images with {len(products)} products",
            correlation_id=correlation_id
        )
        
        for product in products:
            sku = product.get('sku')
            if sku and sku in sku_images and sku_images[sku]:
                product['images'] = sku_images[sku]
                logger.debug(
                    f"Added {len(sku_images[sku])} images to product {sku}",
                    correlation_id=correlation_id
                )
        
        return products
