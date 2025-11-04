"""
Unit tests for variation router endpoints
Tests variation CRUD operations and filtering
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


@patch('src.routers.variation_router.require_admin')
@patch('src.routers.variation_router.create_parent_with_variations')
class TestVariationRouter:
    """Tests for variation management endpoints"""
    
    def test_create_parent_with_variations(self, mock_create, mock_auth):
        """Test creating parent product with variations"""
        mock_auth.return_value = {"user_id": "admin123"}
        parent_id = str(ObjectId())
        mock_create.return_value = AsyncMock(return_value=parent_id)
        
        parent_data = {
            "name": "T-Shirt",
            "brand": "Brand",
            "department": "Clothing",
            "category": "Tops",
            "variation_theme": "color-size",
            "base_price": 19.99,
            "variations": [
                {
                    "sku": "TSHIRT-BLK-S",
                    "name": "T-Shirt - Black, Small",
                    "price": 19.99,
                    "attributes": [
                        {"name": "Color", "value": "Black"},
                        {"name": "Size", "value": "S"}
                    ]
                }
            ]
        }
        
        response = client.post("/api/variations/parent-products", json=parent_data)
        
        assert response.status_code == 200
        assert 'parent_id' in response.json()
    
    @patch('src.routers.variation_router.get_parent_with_variations')
    def test_get_parent_with_variations(self, mock_get, mock_auth):
        """Test retrieving parent with variation matrix"""
        mock_auth.return_value = {"user_id": "user123"}
        parent_id = str(ObjectId())
        mock_get.return_value = AsyncMock(return_value={
            "parent_id": parent_id,
            "name": "T-Shirt",
            "variations": [],
            "total_variations": 0
        })
        
        response = client.get(f"/api/variations/parent-products/{parent_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert 'variations' in data
    
    @patch('src.routers.variation_router.add_variation_to_parent')
    def test_add_variation_to_parent(self, mock_add, mock_auth):
        """Test adding variation to existing parent"""
        mock_auth.return_value = {"user_id": "admin123"}
        parent_id = str(ObjectId())
        variation_id = str(ObjectId())
        mock_add.return_value = AsyncMock(return_value=variation_id)
        
        variation_data = {
            "sku": "TSHIRT-BLK-M",
            "name": "T-Shirt - Black, Medium",
            "price": 19.99,
            "attributes": [
                {"name": "Color", "value": "Black"},
                {"name": "Size", "value": "M"}
            ]
        }
        
        response = client.post(
            f"/api/variations/parent-products/{parent_id}/variations",
            json=variation_data
        )
        
        assert response.status_code == 200
