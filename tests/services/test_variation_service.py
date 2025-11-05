"""
Unit tests for Product Variation Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from src.services.variation_service import VariationService
from src.models.variation import (
    VariationType,
    CreateVariationRequest,
    UpdateVariationRequest,
    VariantAttribute,
    BulkCreateVariationsRequest
)
from src.core.errors import ErrorResponse


@pytest.fixture
def mock_repository():
    """Mock product repository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def variation_service(mock_repository):
    """Variation service instance with mocked repository"""
    return VariationService(mock_repository)


@pytest.fixture
def parent_product():
    """Sample parent product"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Test Product",
        "price": 29.99,
        "variation_type": VariationType.PARENT,
        "department": "Electronics",
        "category": "Phones",
        "brand": "TestBrand",
        "status": "active",
        "description": "Test description",
        "images": [],
        "attributes": {},
        "specifications": {},
        "tags": [],
        "search_keywords": [],
        "seo": None,
        "restrictions": None,
        "child_skus": [],
        "child_count": 0
    }


@pytest.fixture
def child_product():
    """Sample child product"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "name": "Test Product - Red",
        "sku": "TEST-RED",
        "price": 29.99,
        "variation_type": VariationType.CHILD,
        "parent_id": "507f1f77bcf86cd799439011",
        "variant_attributes": [
            {"name": "color", "value": "red"}
        ],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


class TestCreateVariation:
    """Test create_variation method"""
    
    @pytest.mark.asyncio
    async def test_create_variation_success(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test successfully creating a variation"""
        # Setup mocks
        mock_repository.find_by_id.return_value = parent_product
        mock_repository.is_sku_unique.return_value = True
        mock_repository.create.return_value = "child123"
        mock_repository.find_many.return_value = []
        mock_repository.update.return_value = None
        
        request = CreateVariationRequest(
            parent_id="507f1f77bcf86cd799439011",
            name="Test Product - Red",
            sku="TEST-RED",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        
        # Execute
        result = await variation_service.create_variation(
            request=request,
            acting_user="user123"
        )
        
        # Verify
        assert result == "child123"
        mock_repository.find_by_id.assert_called_once()
        mock_repository.is_sku_unique.assert_called_once_with("TEST-RED", None)
        mock_repository.create.assert_called_once()
        mock_repository.update.assert_called_once()  # Updates parent
    
    @pytest.mark.asyncio
    async def test_create_variation_parent_not_found(
        self,
        variation_service,
        mock_repository
    ):
        """Test error when parent product doesn't exist"""
        mock_repository.find_by_id.return_value = None
        
        request = CreateVariationRequest(
            parent_id="nonexistent",
            name="Test",
            sku="TEST",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.create_variation(
                request=request,
                acting_user="user123"
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_variation_parent_not_parent_type(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test error when parent is not a parent type"""
        parent_product["variation_type"] = VariationType.STANDALONE
        mock_repository.find_by_id.return_value = parent_product
        
        request = CreateVariationRequest(
            parent_id="507f1f77bcf86cd799439011",
            name="Test",
            sku="TEST",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.create_variation(
                request=request,
                acting_user="user123"
            )
        
        assert exc_info.value.status_code == 400
        assert "parent" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_variation_sku_already_exists(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test error when SKU already exists"""
        mock_repository.find_by_id.return_value = parent_product
        mock_repository.is_sku_unique.return_value = False
        
        request = CreateVariationRequest(
            parent_id="507f1f77bcf86cd799439011",
            name="Test",
            sku="EXISTING-SKU",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.create_variation(
                request=request,
                acting_user="user123"
            )
        
        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_variation_inherits_parent_data(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test that child inherits parent's data"""
        mock_repository.find_by_id.return_value = parent_product
        mock_repository.is_sku_unique.return_value = True
        mock_repository.create.return_value = "child123"
        mock_repository.find_many.return_value = []
        mock_repository.update.return_value = None
        
        request = CreateVariationRequest(
            parent_id="507f1f77bcf86cd799439011",
            name="Child Product",
            sku="CHILD-SKU",
            variant_attributes=[
                VariantAttribute(name="color", value="red")
            ]
        )
        
        await variation_service.create_variation(
            request=request,
            acting_user="user123"
        )
        
        # Check that create was called with inherited data
        create_call_args = mock_repository.create.call_args[0][0]
        assert create_call_args["department"] == parent_product["department"]
        assert create_call_args["category"] == parent_product["category"]
        assert create_call_args["brand"] == parent_product["brand"]
        assert create_call_args["price"] == parent_product["price"]
        assert create_call_args["variation_type"] == VariationType.CHILD
        assert create_call_args["parent_id"] == "507f1f77bcf86cd799439011"


class TestUpdateVariation:
    """Test update_variation method"""
    
    @pytest.mark.asyncio
    async def test_update_variation_success(
        self,
        variation_service,
        mock_repository,
        child_product
    ):
        """Test successfully updating a variation"""
        mock_repository.find_by_id.return_value = child_product
        mock_repository.update.return_value = {**child_product, "name": "Updated Name"}
        mock_repository.find_many.return_value = []
        
        request = UpdateVariationRequest(name="Updated Name", price=39.99)
        
        result = await variation_service.update_variation(
            variation_id="507f1f77bcf86cd799439012",
            request=request,
            acting_user="user123"
        )
        
        assert result is not None
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_variation_not_found(
        self,
        variation_service,
        mock_repository
    ):
        """Test error when variation doesn't exist"""
        mock_repository.find_by_id.return_value = None
        
        request = UpdateVariationRequest(name="Updated")
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.update_variation(
                variation_id="nonexistent",
                request=request,
                acting_user="user123"
            )
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_variation_not_child_type(
        self,
        variation_service,
        mock_repository,
        child_product
    ):
        """Test error when product is not a child"""
        child_product["variation_type"] = VariationType.PARENT
        mock_repository.find_by_id.return_value = child_product
        
        request = UpdateVariationRequest(name="Updated")
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.update_variation(
                variation_id="507f1f77bcf86cd799439012",
                request=request,
                acting_user="user123"
            )
        
        assert exc_info.value.status_code == 400
        assert "not a variation" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_variation_no_fields(
        self,
        variation_service,
        mock_repository,
        child_product
    ):
        """Test error when no fields to update"""
        mock_repository.find_by_id.return_value = child_product
        
        request = UpdateVariationRequest()  # No fields set
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.update_variation(
                variation_id="507f1f77bcf86cd799439012",
                request=request,
                acting_user="user123"
            )
        
        assert exc_info.value.status_code == 400
        assert "no fields" in str(exc_info.value).lower()


class TestGetVariationRelationship:
    """Test get_variation_relationship method"""
    
    @pytest.mark.asyncio
    async def test_get_relationship_for_parent(
        self,
        variation_service,
        mock_repository,
        parent_product,
        child_product
    ):
        """Test getting relationship for parent product"""
        mock_repository.find_by_id.return_value = parent_product
        mock_repository.find_many.return_value = [child_product]
        
        result = await variation_service.get_variation_relationship(
            product_id="507f1f77bcf86cd799439011"
        )
        
        assert result.parent.product_id == "507f1f77bcf86cd799439011"
        assert len(result.children) == 1
        assert result.children[0].product_id == "507f1f77bcf86cd799439012"
        assert result.attribute_matrix is not None
    
    @pytest.mark.asyncio
    async def test_get_relationship_for_child(
        self,
        variation_service,
        mock_repository,
        parent_product,
        child_product
    ):
        """Test getting relationship for child product"""
        # First call returns child, second call returns parent
        mock_repository.find_by_id.side_effect = [child_product, parent_product]
        mock_repository.find_many.return_value = [child_product]
        
        result = await variation_service.get_variation_relationship(
            product_id="507f1f77bcf86cd799439012"
        )
        
        assert result.parent.product_id == "507f1f77bcf86cd799439011"
        assert len(result.children) == 1
    
    @pytest.mark.asyncio
    async def test_get_relationship_for_standalone(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test getting relationship for standalone product"""
        parent_product["variation_type"] = VariationType.STANDALONE
        mock_repository.find_by_id.return_value = parent_product
        
        result = await variation_service.get_variation_relationship(
            product_id="507f1f77bcf86cd799439011"
        )
        
        assert len(result.children) == 0
    
    @pytest.mark.asyncio
    async def test_get_relationship_product_not_found(
        self,
        variation_service,
        mock_repository
    ):
        """Test error when product doesn't exist"""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await variation_service.get_variation_relationship(
                product_id="nonexistent"
            )
        
        assert exc_info.value.status_code == 404


class TestBulkCreateVariations:
    """Test bulk_create_variations method"""
    
    @pytest.mark.asyncio
    async def test_bulk_create_success(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test successful bulk creation"""
        mock_repository.find_by_id.return_value = parent_product
        mock_repository.is_sku_unique.return_value = True
        mock_repository.create.side_effect = ["child1", "child2", "child3"]
        mock_repository.find_many.return_value = []
        mock_repository.update.return_value = None
        
        request = BulkCreateVariationsRequest(
            parent_id="507f1f77bcf86cd799439011",
            variations=[
                CreateVariationRequest(
                    parent_id="507f1f77bcf86cd799439011",
                    name="Red",
                    sku="RED",
                    variant_attributes=[VariantAttribute(name="color", value="red")]
                ),
                CreateVariationRequest(
                    parent_id="507f1f77bcf86cd799439011",
                    name="Blue",
                    sku="BLUE",
                    variant_attributes=[VariantAttribute(name="color", value="blue")]
                ),
                CreateVariationRequest(
                    parent_id="507f1f77bcf86cd799439011",
                    name="Green",
                    sku="GREEN",
                    variant_attributes=[VariantAttribute(name="color", value="green")]
                )
            ]
        )
        
        result = await variation_service.bulk_create_variations(
            request=request,
            acting_user="user123"
        )
        
        assert result.success_count == 3
        assert result.failure_count == 0
        assert len(result.created_ids) == 3
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_bulk_create_partial_failure(
        self,
        variation_service,
        mock_repository,
        parent_product
    ):
        """Test bulk creation with some failures"""
        mock_repository.find_by_id.return_value = parent_product
        
        # First succeeds, second fails (SKU exists), third succeeds
        mock_repository.is_sku_unique.side_effect = [True, False, True]
        mock_repository.create.side_effect = ["child1", "child3"]
        mock_repository.find_many.return_value = []
        mock_repository.update.return_value = None
        
        request = BulkCreateVariationsRequest(
            parent_id="507f1f77bcf86cd799439011",
            variations=[
                CreateVariationRequest(
                    parent_id="507f1f77bcf86cd799439011",
                    name="Red",
                    sku="RED",
                    variant_attributes=[VariantAttribute(name="color", value="red")]
                ),
                CreateVariationRequest(
                    parent_id="507f1f77bcf86cd799439011",
                    name="Blue",
                    sku="EXISTING",  # Will fail
                    variant_attributes=[VariantAttribute(name="color", value="blue")]
                ),
                CreateVariationRequest(
                    parent_id="507f1f77bcf86cd799439011",
                    name="Green",
                    sku="GREEN",
                    variant_attributes=[VariantAttribute(name="color", value="green")]
                )
            ]
        )
        
        result = await variation_service.bulk_create_variations(
            request=request,
            acting_user="user123"
        )
        
        assert result.success_count == 2
        assert result.failure_count == 1
        assert len(result.created_ids) == 2
        assert len(result.errors) == 1
        assert result.errors[0].variation_index == 1
