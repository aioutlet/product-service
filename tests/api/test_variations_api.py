"""
Unit tests for Product Variation API Endpoints
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.main import app
from src.models.variation import (
    VariationType,
    VariantAttribute,
    ProductVariationSummary,
    VariationRelationship,
    BulkCreateVariationsResponse
)


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication"""
    return {
        "user_id": "admin123",
        "username": "admin",
        "roles": ["admin"],
        "has_role": lambda role: role in ["admin", "user"]
    }


@pytest.fixture
def mock_variation_service():
    """Mock variation service"""
    return AsyncMock()


class TestCreateVariationEndpoint:
    """Test POST /api/variations endpoint"""
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_create_variation_success(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user,
        mock_variation_service
    ):
        """Test successful variation creation"""
        # Setup mocks
        mock_get_user.return_value = mock_admin_user
        mock_get_service.return_value = mock_variation_service
        mock_variation_service.create_variation.return_value = "child123"
        
        # Request
        response = client.post(
            "/api/variations",
            json={
                "parent_id": "parent123",
                "name": "Test Product - Red",
                "sku": "TEST-RED",
                "variant_attributes": [
                    {"name": "color", "value": "red"}
                ]
            }
        )
        
        # Verify
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "child123"
        assert data["parent_id"] == "parent123"
        assert data["sku"] == "TEST-RED"
    
    def test_create_variation_missing_auth(self, client):
        """Test creation without authentication fails"""
        response = client.post(
            "/api/variations",
            json={
                "parent_id": "parent123",
                "name": "Test",
                "sku": "TEST",
                "variant_attributes": [
                    {"name": "color", "value": "red"}
                ]
            }
        )
        
        # Should fail without authentication
        assert response.status_code in [401, 403]
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_create_variation_invalid_data(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user
    ):
        """Test creation with invalid data"""
        mock_get_user.return_value = mock_admin_user
        
        # Missing required fields
        response = client.post(
            "/api/variations",
            json={
                "name": "Test"
                # Missing parent_id, sku, variant_attributes
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestUpdateVariationEndpoint:
    """Test PUT /api/variations/{variation_id} endpoint"""
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_update_variation_success(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user,
        mock_variation_service
    ):
        """Test successful variation update"""
        mock_get_user.return_value = mock_admin_user
        mock_get_service.return_value = mock_variation_service
        mock_variation_service.update_variation.return_value = {
            "_id": "child123",
            "name": "Updated Name"
        }
        
        response = client.put(
            "/api/variations/child123",
            json={
                "name": "Updated Name",
                "price": 39.99
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "child123"
        assert "message" in data
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_update_variation_empty_request(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user,
        mock_variation_service
    ):
        """Test update with no fields"""
        mock_get_user.return_value = mock_admin_user
        mock_get_service.return_value = mock_variation_service
        
        from src.core.errors import ErrorResponse
        mock_variation_service.update_variation.side_effect = ErrorResponse(
            "No fields to update",
            status_code=400
        )
        
        response = client.put(
            "/api/variations/child123",
            json={}
        )
        
        assert response.status_code == 400


class TestGetVariationRelationshipEndpoint:
    """Test GET /api/variations/{product_id}/relationship endpoint"""
    
    @patch('src.api.variations.get_variation_service')
    def test_get_relationship_success(
        self,
        mock_get_service,
        client,
        mock_variation_service
    ):
        """Test getting variation relationship"""
        mock_get_service.return_value = mock_variation_service
        
        # Mock relationship response
        relationship = VariationRelationship(
            parent=ProductVariationSummary(
                product_id="parent123",
                product_name="Test Product",
                variation_type=VariationType.PARENT,
                child_count=2
            ),
            children=[
                ProductVariationSummary(
                    product_id="child1",
                    product_name="Test Product - Red",
                    variation_type=VariationType.CHILD,
                    parent_id="parent123",
                    variant_attributes=[
                        VariantAttribute(name="color", value="red")
                    ]
                ),
                ProductVariationSummary(
                    product_id="child2",
                    product_name="Test Product - Blue",
                    variation_type=VariationType.CHILD,
                    parent_id="parent123",
                    variant_attributes=[
                        VariantAttribute(name="color", value="blue")
                    ]
                )
            ]
        )
        mock_variation_service.get_variation_relationship.return_value = relationship
        
        response = client.get("/api/variations/parent123/relationship")
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent"]["product_id"] == "parent123"
        assert len(data["children"]) == 2


class TestBulkCreateVariationsEndpoint:
    """Test POST /api/variations/bulk endpoint"""
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_bulk_create_success(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user,
        mock_variation_service
    ):
        """Test successful bulk creation"""
        mock_get_user.return_value = mock_admin_user
        mock_get_service.return_value = mock_variation_service
        
        bulk_response = BulkCreateVariationsResponse(
            success_count=3,
            failure_count=0,
            created_ids=["child1", "child2", "child3"],
            errors=[]
        )
        mock_variation_service.bulk_create_variations.return_value = bulk_response
        
        response = client.post(
            "/api/variations/bulk",
            json={
                "parent_id": "parent123",
                "variations": [
                    {
                        "parent_id": "parent123",
                        "name": "Red",
                        "sku": "RED",
                        "variant_attributes": [
                            {"name": "color", "value": "red"}
                        ]
                    },
                    {
                        "parent_id": "parent123",
                        "name": "Blue",
                        "sku": "BLUE",
                        "variant_attributes": [
                            {"name": "color", "value": "blue"}
                        ]
                    },
                    {
                        "parent_id": "parent123",
                        "name": "Green",
                        "sku": "GREEN",
                        "variant_attributes": [
                            {"name": "color", "value": "green"}
                        ]
                    }
                ]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 3
        assert data["failure_count"] == 0
        assert len(data["created_ids"]) == 3
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_bulk_create_with_auto_names(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user,
        mock_variation_service
    ):
        """Test bulk creation with auto-generated names"""
        mock_get_user.return_value = mock_admin_user
        mock_get_service.return_value = mock_variation_service
        
        bulk_response = BulkCreateVariationsResponse(
            success_count=2,
            failure_count=0,
            created_ids=["child1", "child2"],
            errors=[]
        )
        mock_variation_service.bulk_create_variations.return_value = bulk_response
        
        response = client.post(
            "/api/variations/bulk",
            json={
                "parent_id": "parent123",
                "auto_generate_names": True,
                "variations": [
                    {
                        "parent_id": "parent123",
                        "name": "placeholder",
                        "sku": "RED",
                        "variant_attributes": [
                            {"name": "color", "value": "red"}
                        ]
                    },
                    {
                        "parent_id": "parent123",
                        "name": "placeholder",
                        "sku": "BLUE",
                        "variant_attributes": [
                            {"name": "color", "value": "blue"}
                        ]
                    }
                ]
            }
        )
        
        assert response.status_code == 201


class TestGetParentChildrenEndpoint:
    """Test GET /api/variations/parent/{parent_id}/children endpoint"""
    
    @patch('src.api.variations.get_product_repository')
    def test_get_children_success(
        self,
        mock_get_repo,
        client
    ):
        """Test getting all children of a parent"""
        mock_repo = AsyncMock()
        mock_get_repo.return_value = mock_repo
        
        mock_repo.find_many.return_value = [
            {
                "_id": "child1",
                "name": "Child 1",
                "sku": "CHILD1",
                "parent_id": "parent123"
            },
            {
                "_id": "child2",
                "name": "Child 2",
                "sku": "CHILD2",
                "parent_id": "parent123"
            }
        ]
        
        response = client.get("/api/variations/parent/parent123/children")
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == "parent123"
        assert data["child_count"] == 2
        assert len(data["children"]) == 2


class TestDeleteVariationEndpoint:
    """Test DELETE /api/variations/{variation_id} endpoint"""
    
    @patch('src.api.variations.get_current_user')
    @patch('src.api.variations.get_variation_service')
    def test_delete_variation_soft_delete(
        self,
        mock_get_service,
        mock_get_user,
        client,
        mock_admin_user,
        mock_variation_service
    ):
        """Test soft deleting a variation"""
        mock_get_user.return_value = mock_admin_user
        mock_get_service.return_value = mock_variation_service
        mock_variation_service.update_variation.return_value = {}
        
        response = client.delete("/api/variations/child123")
        
        assert response.status_code == 204
