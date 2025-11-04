"""
Tests for admin router endpoints.
These tests focus on critical admin functionality with proper mocking.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.main import app


client = TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication"""
    return {"user_id": "admin123", "roles": ["admin"]}


@pytest.fixture
def mock_products_collection():
    """Mock MongoDB products collection"""
    mock_collection = AsyncMock()
    mock_collection.count_documents = AsyncMock()
    return mock_collection


class TestAdminStatistics:
    """Test admin statistics endpoint"""
    
    @patch('src.routers.admin_router.get_products_collection')
    @patch('src.routers.admin_router.require_admin')
    def test_get_product_stats_success(
        self, 
        mock_require_admin, 
        mock_get_collection,
        mock_admin_user,
        mock_products_collection
    ):
        """Test getting product statistics successfully"""
        # Setup mocks
        mock_require_admin.return_value = mock_admin_user
        mock_get_collection.return_value = mock_products_collection
        
        # Mock count_documents to return different values for different queries
        async def count_side_effect(query):
            if query == {}:
                return 100  # Total products
            elif query.get('is_active') == True:
                return 80  # Active products
            elif query.get('is_active') == False:
                return 20  # Inactive products
            return 0
        
        mock_products_collection.count_documents.side_effect = count_side_effect
        
        # Make request
        response = client.get("/api/admin/stats")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['total_products'] == 100
        assert data['active_products'] == 80
        assert data['inactive_products'] == 20


class TestBadgeManagement:
    """Test badge management endpoints"""
    
    @patch('src.routers.admin_router.get_products_collection')
    @patch('src.routers.admin_router.require_admin')
    @patch('src.routers.admin_router.get_dapr_publisher')
    def test_assign_badge_success(
        self,
        mock_get_publisher,
        mock_require_admin,
        mock_get_collection,
        mock_admin_user,
        mock_products_collection
    ):
        """Test assigning badge to product successfully"""
        # Setup mocks
        mock_require_admin.return_value = mock_admin_user
        mock_get_collection.return_value = mock_products_collection
        
        # Mock publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish = AsyncMock()
        mock_get_publisher.return_value = mock_publisher
        
        # Mock finding the product
        mock_product = {
            "_id": "507f1f77bcf86cd799439011",
            "sku": "TEST-001",
            "name": "Test Product",
            "badges": []
        }
        mock_products_collection.find_one = AsyncMock(return_value=mock_product)
        
        # Mock update
        mock_products_collection.update_one = AsyncMock()
        
        # Request payload
        badge_data = {
            "badge_type": "featured",
            "expires_at": "2025-12-31T23:59:59Z"
        }
        
        # Make request
        response = client.post(
            "/api/admin/products/507f1f77bcf86cd799439011/badges",
            json=badge_data
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Badge assigned successfully'
        assert data['product_id'] == '507f1f77bcf86cd799439011'
        assert data['badge_type'] == 'featured'


class TestBulkImport:
    """Test bulk import endpoints"""
    
    @patch('src.routers.admin_router.require_admin')
    @patch('src.routers.admin_router.generate_template')
    def test_download_template_success(
        self,
        mock_generate_template,
        mock_require_admin,
        mock_admin_user
    ):
        """Test downloading import template"""
        # Setup mocks
        mock_require_admin.return_value = mock_admin_user
        
        # Mock template generation
        from io import BytesIO
        mock_wb = MagicMock()
        mock_generate_template.return_value = mock_wb
        
        mock_buffer = BytesIO(b"fake excel content")
        mock_wb.save = MagicMock(side_effect=lambda buf: buf.write(b"fake excel content"))
        
        # Make request
        response = client.get("/api/admin/bulk-import/template?category=Electronics")
        
        # Assertions
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'content-disposition' in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
