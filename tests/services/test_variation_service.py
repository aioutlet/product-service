"""
Unit Tests for Product Variation Service
Tests PRD REQ-8.1 to REQ-8.5: Product Variations
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.variation_service import VariationService
from src.models.variation_models import (
    ParentProductCreate,
    VariationCreate,
    VariationAttribute,
    VariationTheme,
    VariationUpdate
)


class TestVariationService:
    """Test suite for variation service"""
    
    @pytest.fixture
    def variation_service(self):
        """Create variation service instance"""
        service = VariationService()
        service.products_collection = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_variation_attributes(self):
        """Sample variation attributes"""
        return [
            VariationAttribute(
                name="Color",
                display_name="Color",
                value="Black",
                sort_order=0
            ),
            VariationAttribute(
                name="Size",
                display_name="Size",
                value="M",
                sort_order=1
            )
        ]
    
    @pytest.fixture
    def sample_variations(self, sample_variation_attributes):
        """Sample variations for testing"""
        return [
            VariationCreate(
                sku="TEST-BLK-M",
                name="Test Product - Black, M",
                price=29.99,
                attributes=sample_variation_attributes,
                images=["image1.jpg"]
            ),
            VariationCreate(
                sku="TEST-BLK-L",
                name="Test Product - Black, L",
                price=29.99,
                attributes=[
                    VariationAttribute(
                        name="Color",
                        display_name="Color",
                        value="Black",
                        sort_order=0
                    ),
                    VariationAttribute(
                        name="Size",
                        display_name="Size",
                        value="L",
                        sort_order=1
                    )
                ],
                images=["image2.jpg"]
            )
        ]
    
    @pytest.fixture
    def sample_parent_data(self, sample_variations):
        """Sample parent product data for testing"""
        return ParentProductCreate(
            name="Test Product",
            description="Test product description",
            brand="Test Brand",
            department="Clothing",
            category="Shirts",
            subcategory="T-Shirts",
            variation_theme=VariationTheme.COLOR_SIZE,
            base_price=29.99,
            images=["parent-image.jpg"],
            tags=["test", "sample"],
            specifications={"material": "cotton"},
            variations=sample_variations
        )
    
    @pytest.mark.asyncio
    async def test_create_parent_with_variations_success(
        self,
        variation_service,
        sample_parent_data
    ):
        """Test REQ-8.5: Create parent product with variations successfully"""
        # Mock database calls
        variation_service.products_collection.count_documents = AsyncMock(
            return_value=0
        )
        variation_service.products_collection.insert_one = AsyncMock()
        
        # Execute
        result = await variation_service.create_parent_with_variations(
            parent_data=sample_parent_data,
            created_by="admin-123"
        )
        
        # Assert
        assert 'parent_id' in result
        assert 'variation_ids' in result
        assert result['variation_count'] == 2
        assert len(result['variation_ids']) == 2
        
        # Verify database calls
        assert variation_service.products_collection.insert_one.call_count == 3  # 1 parent + 2 variations
    
    @pytest.mark.asyncio
    async def test_create_parent_duplicate_sku_validation(
        self,
        variation_service,
        sample_parent_data
    ):
        """Test REQ-8.5: Validate SKU uniqueness across variations"""
        # Mock existing SKU
        variation_service.products_collection.count_documents = AsyncMock(
            return_value=1
        )
        
        # Execute and assert
        with pytest.raises(ValueError, match="SKUs already exist"):
            await variation_service.create_parent_with_variations(
                parent_data=sample_parent_data,
                created_by="admin-123"
            )
    
    @pytest.mark.asyncio
    async def test_create_parent_duplicate_variation_attributes(
        self,
        variation_service
    ):
        """Test REQ-8.5: Validate no duplicate attribute combinations"""
        # Create parent with duplicate attribute combinations
        duplicate_variations = [
            VariationCreate(
                sku="TEST-001",
                name="Test 1",
                price=29.99,
                attributes=[
                    VariationAttribute(
                        name="Color",
                        display_name="Color",
                        value="Black",
                        sort_order=0
                    ),
                    VariationAttribute(
                        name="Size",
                        display_name="Size",
                        value="M",
                        sort_order=1
                    )
                ]
            ),
            VariationCreate(
                sku="TEST-002",
                name="Test 2",
                price=29.99,
                attributes=[
                    VariationAttribute(
                        name="Color",
                        display_name="Color",
                        value="Black",
                        sort_order=0
                    ),
                    VariationAttribute(
                        name="Size",
                        display_name="Size",
                        value="M",  # Duplicate combination!
                        sort_order=1
                    )
                ]
            )
        ]
        
        parent_data = ParentProductCreate(
            name="Test Product",
            description="Test",
            brand="Test Brand",
            variation_theme=VariationTheme.COLOR_SIZE,
            variations=duplicate_variations
        )
        
        variation_service.products_collection.count_documents = AsyncMock(
            return_value=0
        )
        
        # Execute and assert
        with pytest.raises(ValueError, match="Duplicate variation attribute"):
            await variation_service.create_parent_with_variations(
                parent_data=parent_data,
                created_by="admin-123"
            )
    
    @pytest.mark.asyncio
    async def test_variation_inheritance_from_parent(
        self,
        variation_service,
        sample_parent_data
    ):
        """Test REQ-8.3: Child products inherit from parent"""
        variation_service.products_collection.count_documents = AsyncMock(
            return_value=0
        )
        
        inserted_docs = []
        
        async def mock_insert(doc):
            inserted_docs.append(doc)
        
        variation_service.products_collection.insert_one = AsyncMock(
            side_effect=mock_insert
        )
        
        # Execute
        await variation_service.create_parent_with_variations(
            parent_data=sample_parent_data,
            created_by="admin-123"
        )
        
        # Verify inheritance in variation documents (skip parent)
        variation_doc1 = inserted_docs[1]
        variation_doc2 = inserted_docs[2]
        
        # Check inherited fields (REQ-8.3)
        assert variation_doc1['brand'] == sample_parent_data.brand
        assert variation_doc1['department'] == sample_parent_data.department
        assert variation_doc1['category'] == sample_parent_data.category
        assert variation_doc1['subcategory'] == sample_parent_data.subcategory
        
        # Check non-inherited fields (REQ-8.3)
        assert variation_doc1['sku'] != variation_doc2['sku']
        assert variation_doc1['price'] == sample_parent_data.variations[0].price
        assert variation_doc1['images'] == sample_parent_data.variations[0].images
        
        # Check merged tags
        assert 'test' in variation_doc1['tags']  # Inherited from parent
        assert 'sample' in variation_doc1['tags']  # Inherited from parent
    
    @pytest.mark.asyncio
    async def test_get_parent_with_variations(self, variation_service):
        """Test REQ-8.4: Get parent product with variation matrix"""
        # Mock parent document
        parent_doc = {
            '_id': '507f1f77bcf86cd799439011',
            'name': 'Test Product',
            'description': 'Test description',
            'brand': 'Test Brand',
            'department': 'Clothing',
            'category': 'Shirts',
            'subcategory': 'T-Shirts',
            'variation_theme': 'color-size',
            'images': ['parent-image.jpg'],
            'tags': ['test'],
            'specifications': {'material': 'cotton'},
            'is_parent': True,
            'is_active': True
        }
        
        # Mock variation documents
        variation_docs = [
            {
                'sku': 'TEST-BLK-M',
                'price': 29.99,
                'variation_attributes_dict': {'color': 'Black', 'size': 'M'},
                'images': ['var1.jpg'],
                'availability': {'status': 'in_stock'}
            },
            {
                'sku': 'TEST-BLK-L',
                'price': 29.99,
                'variation_attributes_dict': {'color': 'Black', 'size': 'L'},
                'images': ['var2.jpg'],
                'availability': {'status': 'out_of_stock'}
            }
        ]
        
        variation_service.products_collection.find_one = AsyncMock(
            return_value=parent_doc
        )
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=variation_docs)
        variation_service.products_collection.find = MagicMock(
            return_value=mock_cursor
        )
        
        # Execute
        result = await variation_service.get_parent_with_variations('507f1f77bcf86cd799439011')
        
        # Assert
        assert result is not None
        assert result.parent_id == '507f1f77bcf86cd799439011'
        assert result.name == 'Test Product'
        assert result.total_variations == 2
        assert len(result.variations) == 2
        
        # Check variation matrix (REQ-8.4)
        assert result.variations[0].sku == 'TEST-BLK-M'
        assert result.variations[0].attributes == {'color': 'Black', 'size': 'M'}
        assert result.variations[0].available is True  # in_stock
        assert result.variations[1].available is False  # out_of_stock
    
    @pytest.mark.asyncio
    async def test_add_variation_to_parent(self, variation_service):
        """Test REQ-8.5: Add new variation to existing parent"""
        # Mock parent document
        parent_doc = {
            '_id': '507f1f77bcf86cd799439011',
            'name': 'Test Product',
            'description': 'Test description',
            'brand': 'Test Brand',
            'department': 'Clothing',
            'category': 'Shirts',
            'variation_theme': 'color-size',
            'base_price': 29.99,
            'images': [],
            'tags': [],
            'specifications': {},
            'is_parent': True,
            'is_active': True
        }
        
        # Mock existing variations (for uniqueness check)
        existing_variations = [
            {
                'variation_attributes': [
                    {'name': 'Color', 'value': 'Black'},
                    {'name': 'Size', 'value': 'M'}
                ]
            }
        ]
        
        variation_service.products_collection.find_one = AsyncMock(
            return_value=parent_doc
        )
        variation_service.products_collection.count_documents = AsyncMock(
            return_value=0
        )
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=existing_variations)
        variation_service.products_collection.find = MagicMock(
            return_value=mock_cursor
        )
        variation_service.products_collection.insert_one = AsyncMock()
        variation_service.products_collection.update_one = AsyncMock()
        
        # New variation with different size
        new_variation = VariationCreate(
            sku="TEST-BLK-L",
            name="Test Product - Black, L",
            price=29.99,
            attributes=[
                VariationAttribute(
                    name="Color",
                    display_name="Color",
                    value="Black",
                    sort_order=0
                ),
                VariationAttribute(
                    name="Size",
                    display_name="Size",
                    value="L",  # Different from existing
                    sort_order=1
                )
            ]
        )
        
        # Execute
        variation_id = await variation_service.add_variation_to_parent(
            parent_id='507f1f77bcf86cd799439011',
            variation=new_variation,
            created_by='admin-123'
        )
        
        # Assert
        assert variation_id is not None
        variation_service.products_collection.insert_one.assert_called_once()
        variation_service.products_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_duplicate_variation_fails(self, variation_service):
        """Test REQ-8.5: Cannot add variation with duplicate attributes"""
        parent_doc = {
            '_id': '507f1f77bcf86cd799439011',
            'name': 'Test Product',
            'brand': 'Test Brand',
            'variation_theme': 'color-size',
            'is_parent': True,
            'is_active': True
        }
        
        # Existing variation with same attributes
        existing_variations = [
            {
                'variation_attributes': [
                    {'name': 'Color', 'value': 'Black'},
                    {'name': 'Size', 'value': 'M'}
                ]
            }
        ]
        
        variation_service.products_collection.find_one = AsyncMock(
            return_value=parent_doc
        )
        variation_service.products_collection.count_documents = AsyncMock(
            return_value=0
        )
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=existing_variations)
        variation_service.products_collection.find = MagicMock(
            return_value=mock_cursor
        )
        
        # Try to add duplicate variation
        duplicate_variation = VariationCreate(
            sku="TEST-BLK-M-2",
            name="Test Product - Black, M (duplicate)",
            price=29.99,
            attributes=[
                VariationAttribute(name="Color", display_name="Color", value="Black", sort_order=0),
                VariationAttribute(name="Size", display_name="Size", value="M", sort_order=1)
            ]
        )
        
        # Execute and assert
        with pytest.raises(ValueError, match="same attributes already exists"):
            await variation_service.add_variation_to_parent(
                parent_id='507f1f77bcf86cd799439011',
                variation=duplicate_variation,
                created_by='admin-123'
            )
    
    @pytest.mark.asyncio
    async def test_update_variation(self, variation_service):
        """Test REQ-8.5: Update variation attributes"""
        mock_result = MagicMock()
        mock_result.modified_count = 1
        variation_service.products_collection.update_one = AsyncMock(
            return_value=mock_result
        )
        
        updates = VariationUpdate(
            price=39.99,
            images=["new-image.jpg"]
        )
        
        # Execute
        success = await variation_service.update_variation(
            variation_id='507f1f77bcf86cd799439022',
            updates=updates,
            updated_by='admin-123'
        )
        
        # Assert
        assert success is True
        variation_service.products_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_variation(self, variation_service):
        """Test REQ-8.5: Soft delete variation"""
        # Mock variation document
        variation_doc = {
            '_id': '507f1f77bcf86cd799439022',
            'parent_id': '507f1f77bcf86cd799439011',
            'is_variation': True
        }
        
        mock_result = MagicMock()
        mock_result.modified_count = 1
        
        variation_service.products_collection.find_one = AsyncMock(
            return_value=variation_doc
        )
        variation_service.products_collection.update_one = AsyncMock(
            return_value=mock_result
        )
        
        # Execute
        success = await variation_service.delete_variation(
            variation_id='507f1f77bcf86cd799439022',
            deleted_by='admin-123'
        )
        
        # Assert
        assert success is True
        # Should update both variation and parent
        assert variation_service.products_collection.update_one.call_count == 2
    
    @pytest.mark.asyncio
    async def test_filter_variations_by_attributes(self, variation_service):
        """Test REQ-8.4: Filter variations by attribute values"""
        # Mock filtered variations
        filtered_variations = [
            {
                'sku': 'TEST-BLK-M',
                'price': 29.99,
                'variation_attributes_dict': {'color': 'Black', 'size': 'M'},
                'images': ['var1.jpg'],
                'availability': {'status': 'in_stock'}
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=filtered_variations)
        variation_service.products_collection.find = MagicMock(
            return_value=mock_cursor
        )
        
        # Execute
        result = await variation_service.filter_variations(
            parent_id='507f1f77bcf86cd799439011',
            attribute_filters={'color': 'Black', 'size': 'M'}
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].sku == 'TEST-BLK-M'
        assert result[0].attributes == {'color': 'Black', 'size': 'M'}
        assert result[0].available is True
    
    @pytest.mark.asyncio
    async def test_variation_count_limit(self, variation_service):
        """Test REQ-8.1: Support up to 1,000 variations per parent"""
        # Create parent with 1,001 variations (exceeds limit)
        excessive_variations = [
            VariationCreate(
                sku=f"TEST-{i:04d}",
                name=f"Test Product {i}",
                price=29.99,
                attributes=[
                    VariationAttribute(
                        name="Size",
                        display_name="Size",
                        value=f"Size-{i}",
                        sort_order=0
                    )
                ]
            )
            for i in range(1001)
        ]
        
        # Should fail validation at Pydantic level (max_length=1000)
        # The Pydantic ValidationError is raised during object creation
        from pydantic import ValidationError as PydanticValidationError
        
        with pytest.raises(PydanticValidationError) as exc_info:
            ParentProductCreate(
                name="Test Product",
                description="Test",
                brand="Test Brand",
                variation_theme=VariationTheme.SIZE,
                variations=excessive_variations
            )
        
        # Verify it's the right validation error
        assert 'too_long' in str(exc_info.value)
        assert '1000' in str(exc_info.value)
