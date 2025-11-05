"""
Unit tests for product attributes API endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.models.attribute_schema import (
    CategorySchema, AttributeGroup, AttributeCategory,
    AttributeDefinition, AttributeDataType, ProductAttributes
)


@pytest.fixture
def mock_repository():
    """Create mock schema repository"""
    return MagicMock()


@pytest.fixture
def mock_validation_service():
    """Create mock validation service"""
    return MagicMock()


@pytest.fixture
def mock_search_service():
    """Create mock faceted search service"""
    return MagicMock()


@pytest.fixture
def client(mock_repository, mock_validation_service, mock_search_service):
    """Create test client with dependency overrides"""
    from src.api.product_attributes import (
        get_schema_repository,
        get_attribute_validation_service,
        get_faceted_search_service
    )
    
    app.dependency_overrides[get_schema_repository] = lambda: mock_repository
    app.dependency_overrides[get_attribute_validation_service] = lambda: mock_validation_service
    app.dependency_overrides[get_faceted_search_service] = lambda: mock_search_service
    
    yield TestClient(app)
    
    # Clean up
    app.dependency_overrides.clear()


class TestListSchemas:
    """Test GET /api/attributes/schemas"""
    
    @pytest.mark.asyncio
    async def test_list_schemas_success(self, client, mock_repository):
        """Test listing schemas successfully"""
        mock_repository.list_all = AsyncMock(return_value=[
            {
                "_id": "507f1f77bcf86cd799439011",
                "category_name": "Clothing",
                "display_name": "Clothing & Apparel",
                "attribute_groups": [],
                "version": 1,
                "is_active": True
            }
        ])
        
        response = client.get("/api/attributes/schemas")
        
        assert response.status_code == 200
        data = response.json()
        print("DEBUG - Response data:", data)
        assert len(data) == 1
        assert data[0]["category_name"] == "Clothing"
    
    @pytest.mark.asyncio
    async def test_list_schemas_empty(self, client, mock_repository):
        """Test listing schemas when none exist"""
        mock_repository.list_all = AsyncMock(return_value=[])
        
        response = client.get("/api/attributes/schemas")
        
        assert response.status_code == 200
        assert response.json() == []


class TestGetSchema:
    """Test GET /api/attributes/schemas/{category}"""
    
    @pytest.mark.asyncio
    async def test_get_schema_success(self, client, mock_repository):
        """Test getting schema by category"""
        mock_repository.get_by_category = AsyncMock(return_value={
            "_id": "507f1f77bcf86cd799439011",
            "category_name": "Clothing",
            "display_name": "Clothing & Apparel",
            "attribute_groups": [],
            "version": 1,
            "is_active": True
        })
        
        response = client.get("/api/attributes/schemas/Clothing")
        
        assert response.status_code == 200
        data = response.json()
        assert data["category_name"] == "Clothing"
    
    @pytest.mark.asyncio
    async def test_get_schema_not_found(self, client, mock_repository):
        """Test getting non-existent schema"""
        mock_repository.get_by_category = AsyncMock(return_value=None)
        
        response = client.get("/api/attributes/schemas/NonExistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateSchema:
    """Test POST /api/attributes/schemas"""
    
    @pytest.mark.asyncio
    async def test_create_schema_success(self, client, mock_repository):
        """Test creating new schema"""
        mock_repository.get_by_category = AsyncMock(return_value=None)
        mock_repository.create = AsyncMock(return_value="507f1f77bcf86cd799439011")
        
        schema_data = {
            "category_name": "NewCategory",
            "display_name": "New Category",
            "attribute_groups": []
        }
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.post("/api/attributes/schemas", json=schema_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "schema_id" in data
        assert data["category"] == "NewCategory"
    
    @pytest.mark.asyncio
    async def test_create_schema_already_exists(self, client, mock_repository):
        """Test creating schema that already exists"""
        mock_repository.get_by_category = AsyncMock(return_value={
            "category_name": "Clothing",
            "display_name": "Clothing"
        })
        
        schema_data = {
            "category_name": "Clothing",
            "display_name": "Clothing & Apparel",
            "attribute_groups": []
        }
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.post("/api/attributes/schemas", json=schema_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_create_schema_invalid_data(self, client):
        """Test creating schema with invalid data"""
        invalid_data = {
            "category_name": "",  # Empty name
            "display_name": "Test"
        }
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.post("/api/attributes/schemas", json=invalid_data)
        
        assert response.status_code == 422


class TestUpdateSchema:
    """Test PUT /api/attributes/schemas/{category}"""
    
    @pytest.mark.asyncio
    async def test_update_schema_success(self, client, mock_repository):
        """Test updating existing schema"""
        mock_repository.get_by_category = AsyncMock(return_value={
            "category_name": "Clothing",
            "display_name": "Old Name",
            "attribute_groups": [],
            "version": 1,
            "is_active": True
        })
        mock_repository.update = AsyncMock()
        
        update_data = {
            "display_name": "New Name",
            "is_active": False
        }
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.put("/api/attributes/schemas/Clothing", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Schema updated successfully"
    
    @pytest.mark.asyncio
    async def test_update_schema_not_found(self, client, mock_repository):
        """Test updating non-existent schema"""
        mock_repository.get_by_category = AsyncMock(return_value=None)
        
        update_data = {
            "display_name": "New Name"
        }
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.put("/api/attributes/schemas/NonExistent", json=update_data)
        
        assert response.status_code == 404


class TestDeleteSchema:
    """Test DELETE /api/attributes/schemas/{category}"""
    
    @pytest.mark.asyncio
    async def test_delete_schema_success(self, client, mock_repository):
        """Test deleting existing schema"""
        mock_repository.get_by_category = AsyncMock(return_value={
            "category_name": "Clothing",
            "display_name": "Clothing"
        })
        mock_repository.delete = AsyncMock()
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.delete("/api/attributes/schemas/Clothing")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Schema deleted successfully"
    
    @pytest.mark.asyncio
    async def test_delete_schema_not_found(self, client, mock_repository):
        """Test deleting non-existent schema"""
        mock_repository.get_by_category = AsyncMock(return_value=None)
        
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.delete("/api/attributes/schemas/NonExistent")
        
        assert response.status_code == 404


class TestValidateAttributes:
    """Test POST /api/attributes/validate"""
    
    def test_validate_attributes_success(self, client, mock_validation_service):
        """Test validating attributes successfully"""
        from src.models.attribute_schema import AttributeValidationResult
        
        mock_validation_service.validate_attributes.return_value = AttributeValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_attributes={"fit_type": "Regular"}
        )
        
        payload = {
            "category": "Clothing",
            "attributes": {
                "category_specific": {
                    "fit_type": "Regular"
                }
            }
        }
        
        response = client.post("/api/attributes/validate", params={"category": "Clothing"}, json=payload["attributes"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
    
    def test_validate_attributes_with_errors(self, client, mock_validation_service):
        """Test validating attributes with errors"""
        from src.models.attribute_schema import AttributeValidationResult, AttributeValidationError
        
        mock_validation_service.validate_attributes.return_value = AttributeValidationResult(
            is_valid=False,
            errors=[
                AttributeValidationError(
                    attribute_name="fit_type",
                    attribute_path="category_specific.fit_type",
                    error_code="INVALID_ENUM_VALUE",
                    error_message="Invalid value"
                )
            ],
            warnings=[]
        )
        
        payload = {
            "category": "Clothing",
            "attributes": {
                "category_specific": {
                    "fit_type": "InvalidFit"
                }
            }
        }
        
        response = client.post("/api/attributes/validate", params={"category": "Clothing"}, json=payload["attributes"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0


class TestFacetedSearch:
    """Test GET /api/attributes/search/faceted"""
    
    @pytest.mark.asyncio
    async def test_faceted_search_success(self, client, mock_search_service):
        """Test faceted search"""
        from src.models.attribute_schema import FacetedSearchResult
        
        mock_search_service.get_available_facets = AsyncMock(return_value=[
            "attributes.category_specific.fit_type"
        ])
        mock_search_service.search_with_facets = AsyncMock(return_value=FacetedSearchResult(
            products=[{"id": "1", "name": "Product 1"}],
            facets=[],
            total_count=1,
            applied_filters={},
            page=1,
            page_size=20
        ))
        
        response = client.get("/api/attributes/search/faceted?category=Clothing&page=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
    
    @pytest.mark.asyncio
    async def test_faceted_search_with_text_query(self, client, mock_search_service):
        """Test faceted search with text query"""
        from src.models.attribute_schema import FacetedSearchResult
        
        mock_search_service.get_available_facets = AsyncMock(return_value=[])
        mock_search_service.search_with_facets = AsyncMock(return_value=FacetedSearchResult(
            products=[],
            facets=[],
            total_count=0,
            applied_filters={},
            page=1,
            page_size=20
        ))
        
        response = client.get("/api/attributes/search/faceted?text_query=shirt&page=1")
        
        assert response.status_code == 200
    
    def test_faceted_search_invalid_pagination(self, client):
        """Test faceted search with invalid pagination"""
        response = client.get("/api/attributes/search/faceted?page=0")
        
        # Should return validation error
        assert response.status_code == 422


class TestGetCategoryFacets:
    """Test GET /api/attributes/facets/{category}"""
    
    @pytest.mark.asyncio
    async def test_get_category_facets_success(self, client, mock_search_service):
        """Test getting facets for category"""
        mock_search_service.get_available_facets = AsyncMock(return_value=[
            "attributes.category_specific.fit_type",
            "attributes.category_specific.neckline",
            "attributes.materials_composition.primary_material"
        ])
        
        response = client.get("/api/attributes/facets/Clothing")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3


class TestAuthorizationRequired:
    """Test endpoints requiring admin authorization"""
    
    def test_create_schema_requires_auth(self, client):
        """Test create schema requires admin"""
        schema_data = {
            "category_name": "Test",
            "display_name": "Test",
            "attribute_groups": []
        }
        
        # Without admin mock, should fail
        response = client.post("/api/attributes/schemas", json=schema_data)
        assert response.status_code in [401, 403]
    
    def test_update_schema_requires_auth(self, client):
        """Test update schema requires admin"""
        update_data = {"display_name": "New Name"}
        
        response = client.put("/api/attributes/schemas/Clothing", json=update_data)
        assert response.status_code in [401, 403]
    
    def test_delete_schema_requires_auth(self, client):
        """Test delete schema requires admin"""
        response = client.delete("/api/attributes/schemas/Clothing")
        assert response.status_code in [401, 403]


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, client, mock_repository):
        """Test handling database errors"""
        mock_repository.list_all = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.get("/api/attributes/schemas")
        
        assert response.status_code == 500
    
    def test_invalid_json_handling(self, client):
        """Test handling invalid JSON"""
        with patch("src.api.product_attributes.require_admin", return_value=True):
            response = client.post(
                "/api/attributes/schemas",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 422
