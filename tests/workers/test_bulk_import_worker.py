"""
Unit tests for bulk import background worker
Tests batch processing, job status updates, and error handling
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId
from src.workers.bulk_import_worker import BulkImportWorker


@pytest.fixture
def mock_collections():
    """Mock MongoDB collections"""
    with patch('src.workers.bulk_import_worker.get_products_collection') as mock_products, \
         patch('src.workers.bulk_import_worker.get_import_jobs_collection') as mock_jobs:
        yield mock_products.return_value, mock_jobs.return_value


@pytest.fixture
def sample_products():
    """Sample product data for import"""
    return [
        {
            "sku": "PROD-001",
            "name": "Product 1",
            "price": 19.99,
            "brand": "Brand A",
            "department": "Electronics",
            "category": "Phones"
        },
        {
            "sku": "PROD-002",
            "name": "Product 2",
            "price": 29.99,
            "brand": "Brand B",
            "department": "Electronics",
            "category": "Tablets"
        }
    ]


@pytest.mark.asyncio
class TestBulkImportWorker:
    """Tests for bulk import worker"""
    
    @patch('src.workers.bulk_import_worker.get_dapr_publisher')
    async def test_process_import_job_partial_mode(self, mock_publisher, mock_collections, sample_products):
        """Test processing import job in partial mode"""
        mock_products_col, mock_jobs_col = mock_collections
        
        mock_pub_instance = Mock()
        mock_pub_instance.publish = AsyncMock()
        mock_publisher.return_value = mock_pub_instance
        
        # Mock SKU checks
        mock_products_col.find_one.return_value = None
        mock_products_col.insert_one.return_value = Mock(inserted_id=ObjectId())
        mock_jobs_col.update_one.return_value = Mock(modified_count=1)
        
        worker = BulkImportWorker()
        job_id = "job-123"
        import_mode = "partial"
        
        await worker.process_import_job(job_id, sample_products, import_mode)
        
        # Verify products were inserted
        assert mock_products_col.insert_one.call_count == len(sample_products)
        
        # Verify job status was updated
        assert mock_jobs_col.update_one.called
    
    @patch('src.workers.bulk_import_worker.get_dapr_publisher')
    async def test_process_batch_with_duplicate_sku(self, mock_publisher, mock_collections, sample_products):
        """Test batch processing handles duplicate SKUs"""
        mock_products_col, mock_jobs_col = mock_collections
        
        mock_pub_instance = Mock()
        mock_pub_instance.publish = AsyncMock()
        mock_publisher.return_value = mock_pub_instance
        
        # Mock first SKU check returns existing product (duplicate)
        mock_products_col.find_one.side_effect = [
            {"_id": ObjectId(), "sku": "PROD-001"},  # Duplicate
            None  # Second SKU is unique
        ]
        mock_products_col.insert_one.return_value = Mock(inserted_id=ObjectId())
        mock_jobs_col.update_one.return_value = Mock(modified_count=1)
        
        worker = BulkImportWorker()
        job_id = "job-123"
        
        await worker.process_import_job(job_id, sample_products, "partial")
        
        # Should skip duplicate and insert only unique
        assert mock_products_col.insert_one.call_count == 1
    
    @patch('src.workers.bulk_import_worker.get_dapr_publisher')
    async def test_progress_event_publishing(self, mock_publisher, mock_collections, sample_products):
        """Test worker publishes progress events"""
        mock_products_col, mock_jobs_col = mock_collections
        
        mock_pub_instance = Mock()
        mock_pub_instance.publish = AsyncMock()
        mock_publisher.return_value = mock_pub_instance
        
        mock_products_col.find_one.return_value = None
        mock_products_col.insert_one.return_value = Mock(inserted_id=ObjectId())
        mock_jobs_col.update_one.return_value = Mock(modified_count=1)
        
        worker = BulkImportWorker()
        await worker.process_import_job("job-123", sample_products, "partial")
        
        # Verify progress and completion events were published
        publish_calls = mock_pub_instance.publish.call_args_list
        event_types = [call[0][0] for call in publish_calls]
        
        assert "product.bulk.import.progress" in event_types or "product.bulk.import.completed" in event_types
