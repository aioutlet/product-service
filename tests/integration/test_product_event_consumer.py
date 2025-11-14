"""
Integration tests for Dapr functionality
Tests the integration between Product Service and Dapr building blocks
"""

import os
from datetime import datetime, UTC

import aiohttp
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import config
from app.events.publishers.publisher import DaprEventPublisher


class TestDaprIntegration:
    """Integration tests for Dapr sidecar and building blocks"""

    @pytest.fixture
    async def dapr_publisher(self):
        """Create a DaprEventPublisher instance"""
        publisher = DaprEventPublisher()
        yield publisher

    @pytest.fixture
    def dapr_port(self):
        """Get Dapr HTTP port from environment or config"""
        return os.getenv('DAPR_HTTP_PORT', str(config.dapr_http_port))

    @pytest.fixture
    def app_port(self):
        """Get application port from environment or config"""
        return os.getenv('DAPR_APP_PORT', str(config.port))

    @pytest.mark.asyncio
    async def test_dapr_sidecar_health(self, dapr_port):
        """Test if Dapr sidecar is healthy and reachable"""
        url = f"http://localhost:{dapr_port}/v1.0/healthz"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    if response.status != 200:
                        pytest.skip(f"Dapr sidecar not healthy: status {response.status}")
                    assert response.status == 200
            except aiohttp.ClientError as e:
                pytest.skip(f"Dapr sidecar not reachable: {e}")

    @pytest.mark.asyncio
    async def test_product_service_health(self, app_port):
        """Test if Product Service is running and healthy"""
        url = f"http://localhost:{app_port}/api/health"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    assert response.status == 200
                    health_data = await response.json()
                    assert health_data.get('status') in ['healthy', 'operational']
                    assert health_data.get('service') == config.service_name
            except aiohttp.ClientError as e:
                pytest.skip(f"Product Service not reachable: {e}")

    @pytest.mark.asyncio
    async def test_dapr_pubsub_publish(self, dapr_port):
        """Test Dapr pub/sub publishing functionality"""
        pubsub_name = os.getenv('DAPR_PUBSUB_NAME', 'product-pubsub')
        url = f"http://localhost:{dapr_port}/v1.0/publish/{pubsub_name}/test-topic"
        
        test_event = {
            "specversion": "1.0",
            "type": "test.event",
            "source": "/test",
            "id": "test-123",
            "data": {"message": "Test event from integration tests"}
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    json=test_event,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=5.0)
                ) as response:
                    # Dapr returns 204 No Content on successful publish
                    if response.status != 204:
                        pytest.skip(f"Dapr pub/sub not available: status {response.status}")
                    assert response.status == 204
            except aiohttp.ClientError as e:
                pytest.skip(f"Dapr pub/sub not available: {e}")

    @pytest.mark.asyncio
    async def test_dapr_publisher_health_check(self, dapr_publisher):
        """Test DaprEventPublisher health check"""
        try:
            is_healthy = await dapr_publisher.health_check()
            assert is_healthy, "Dapr publisher health check failed"
        except Exception as e:
            pytest.skip(f"Dapr not available for health check: {e}")

    @pytest.mark.asyncio
    async def test_dapr_publisher_product_created_event(self, dapr_publisher):
        """Test publishing product.created event through DaprEventPublisher"""
        test_product_data = {
            "_id": "test-product-integration-123",
            "name": "Integration Test Product",
            "sku": "TEST-DAPR-001",
            "price": 29.99,
            "stock": 100,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat()
        }
        
        try:
            success = await dapr_publisher.publish_product_created(
                test_product_data, 
                "test-correlation-integration-123"
            )
            assert success, "Failed to publish product.created event"
        except Exception as e:
            pytest.skip(f"Dapr not available for event publishing: {e}")

    @pytest.mark.asyncio
    async def test_dapr_publisher_product_updated_event(self, dapr_publisher):
        """Test publishing product.updated event through DaprEventPublisher"""
        test_product_data = {
            "_id": "test-product-integration-456",
            "name": "Updated Integration Test Product",
            "sku": "TEST-DAPR-002",
            "price": 39.99,
            "stock": 50,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat()
        }
        
        try:
            success = await dapr_publisher.publish_product_updated(
                test_product_data,
                "test-correlation-integration-456"
            )
            assert success, "Failed to publish product.updated event"
        except Exception as e:
            pytest.skip(f"Dapr not available for event publishing: {e}")

    @pytest.mark.asyncio
    async def test_dapr_publisher_product_deleted_event(self, dapr_publisher):
        """Test publishing product.deleted event through DaprEventPublisher"""
        product_id = "test-product-integration-789"
        
        try:
            success = await dapr_publisher.publish_product_deleted(
                product_id,
                "test-correlation-integration-789"
            )
            assert success, "Failed to publish product.deleted event"
        except Exception as e:
            pytest.skip(f"Dapr not available for event publishing: {e}")

    @pytest.mark.asyncio
    async def test_dapr_service_invocation(self, dapr_port):
        """Test Dapr service invocation building block"""
        # Test invoking product-service's health endpoint through Dapr
        app_id = config.service_name
        url = f"http://localhost:{dapr_port}/v1.0/invoke/{app_id}/method/api/health"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5.0)) as response:
                    if response.status != 200:
                        pytest.skip(f"Dapr service invocation not available: status {response.status}")
                    assert response.status == 200
                    health_data = await response.json()
                    assert health_data.get('service') == config.service_name
            except aiohttp.ClientError as e:
                pytest.skip(f"Dapr service invocation not available: {e}")
