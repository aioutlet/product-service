"""
Unit tests for admin router endpoints - focuses on critical paths
Tests badge management, size charts, restrictions, and statistics
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from bson import ObjectId


@pytest.fixture
def mock_admin_user():
    return {"user_id": "admin123", "role": "admin"}


@patch('src.routers.admin_router.require_admin')
@patch('src.routers.admin_router.get_products_collection')
class TestAdminStats:
    """Tests for admin statistics endpoint"""
    
    def test_get_stats_success(self, mock_collection, mock_auth):
        """Test successful retrieval of admin statistics"""
        from fastapi.testclient import TestClient
        from src.main import app
        
        mock_auth.return_value = {"user_id": "admin123"}
        mock_collection.return_value.count_documents.side_effect = [100, 75, 25]
        
        client = TestClient(app)
        response = client.get("/api/admin/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total_products'] == 100
        assert data['active_products'] == 75
        assert data['inactive_products'] == 25


@patch('src.routers.admin_router.require_admin')
@patch('src.routers.admin_router.get_products_collection')
@patch('src.routers.admin_router.get_dapr_publisher')
class TestBadgeManagement:
    """Tests for badge management"""
    
    def test_assign_badge(self, mock_publisher, mock_collection, mock_auth):
        """Test assigning badge to product"""
        from fastapi.testclient import TestClient
        from src.main import app
        
        mock_auth.return_value = {"user_id": "admin123"}
        mock_pub_instance = Mock()
        mock_pub_instance.publish = AsyncMock()
        mock_publisher.return_value = mock_pub_instance
        
        product_id = str(ObjectId())
        mock_collection.return_value.find_one.return_value = {
            "_id": ObjectId(product_id),
            "name": "Test Product",
            "badges": []
        }
        mock_collection.return_value.update_one.return_value = Mock(modified_count=1)
        
        badge_data = {"badge_type": "featured"}
        
        client = TestClient(app)
        response = client.post(f"/api/admin/products/{product_id}/badges", json=badge_data)
        
        assert response.status_code == 200


@patch('src.routers.admin_router.require_admin')
@patch('src.routers.admin_router.get_size_charts_collection')
class TestSizeChartManagement:
    """Tests for size chart management"""
    
    def test_create_size_chart(self, mock_collection, mock_auth):
        """Test creating size chart"""
        from fastapi.testclient import TestClient
        from src.main import app
        
        mock_auth.return_value = {"user_id": "admin123"}
        chart_id = ObjectId()
        mock_collection.return_value.insert_one.return_value = Mock(inserted_id=chart_id)
        
        chart_data = {
            "category": "Clothing",
            "name": "Men's Sizes",
            "region": "US",
            "format_type": "structured",
            "data": {"S": {"chest": "34-36"}}
        }
        
        client = TestClient(app)
        response = client.post("/api/admin/size-charts", json=chart_data)
        
        assert response.status_code == 200
