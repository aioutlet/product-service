"""
Unit tests for event subscription endpoints
Tests Dapr event handlers for review, inventory, analytics, Q&A events
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


@patch('src.routers.event_subscriptions.get_products_collection')
class TestEventSubscriptions:
    """Tests for Dapr event subscriptions"""
    
    def test_dapr_subscribe_endpoint(self, mock_collection):
        """Test Dapr subscription discovery endpoint"""
        response = client.post("/dapr/subscribe")
        
        assert response.status_code == 200
        subscriptions = response.json()
        assert len(subscriptions) > 0
        assert any(sub['topic'] == 'review.created' for sub in subscriptions)
    
    @patch('src.routers.event_subscriptions.update_review_aggregates')
    def test_handle_review_created(self, mock_update, mock_collection):
        """Test handling review.created event"""
        mock_update.return_value = AsyncMock()
        
        event_data = {
            "eventType": "review.created",
            "data": {
                "productId": str(ObjectId()),
                "rating": 5,
                "verifiedPurchase": True
            }
        }
        
        response = client.post("/events/review-created", json=event_data)
        
        assert response.status_code == 200
        assert response.json()['status'] == 'SUCCESS'
    
    @patch('src.routers.event_subscriptions.update_availability_status')
    def test_handle_inventory_updated(self, mock_update, mock_collection):
        """Test handling inventory.stock.updated event"""
        mock_update.return_value = AsyncMock(return_value=False)
        
        event_data = {
            "eventType": "inventory.stock.updated",
            "data": {
                "sku": "PROD-001",
                "productId": str(ObjectId()),
                "availableQuantity": 100,
                "lowStockThreshold": 10
            }
        }
        
        response = client.post("/events/inventory-updated", json=event_data)
        
        assert response.status_code == 200
        assert response.json()['status'] == 'SUCCESS'
    
    @patch('src.routers.event_subscriptions.evaluate_badge_criteria')
    def test_handle_sales_updated(self, mock_evaluate, mock_collection):
        """Test handling analytics.product.sales.updated event"""
        mock_evaluate.return_value = AsyncMock()
        
        event_data = {
            "eventType": "analytics.product.sales.updated",
            "data": {
                "productId": str(ObjectId()),
                "category": "Electronics",
                "salesLast30Days": 500,
                "categoryRank": 5
            }
        }
        
        response = client.post("/events/sales-updated", json=event_data)
        
        assert response.status_code == 200
        assert response.json()['status'] == 'SUCCESS'


@patch('src.routers.event_subscriptions.get_products_collection')
class TestBulkImportEventHandler:
    """Tests for bulk import event handler"""
    
    @patch('src.routers.event_subscriptions.BulkImportWorker')
    def test_handle_bulk_import_job_created(self, mock_worker, mock_collection):
        """Test handling bulk import job creation event"""
        mock_worker_instance = Mock()
        mock_worker.return_value = mock_worker_instance
        
        event_data = {
            "eventType": "product.bulk.import.job.created",
            "data": {
                "jobId": "job-123",
                "products": [],
                "importMode": "partial"
            }
        }
        
        response = client.post("/events/bulk-import-job-created", json=event_data)
        
        assert response.status_code == 200
