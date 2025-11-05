"""
Test script to verify Dapr publisher functionality
Run this after starting the product service with Dapr sidecar
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.dapr_publisher import get_dapr_publisher


async def test_publish():
    """Test publishing a sample event to Dapr"""
    
    publisher = get_dapr_publisher()
    
    # Sample product created event
    test_data = {
        "productId": "test-product-123",
        "name": "Test Product",
        "sku": "TEST-001",
        "price": 29.99,
        "brand": "Test Brand",
        "category": "Test Category",
        "status": "active"
    }
    
    print("Testing Dapr event publishing...")
    print(f"Dapr URL: {publisher.dapr_url}")
    print(f"PubSub Name: {publisher.dapr_pubsub_name}")
    print(f"Topic: product.created")
    print(f"Event Type: com.aioutlet.product.created.v1")
    print("-" * 60)
    
    # Publish test event
    success = await publisher.publish(
        topic="product.created",
        data=test_data,
        event_type="com.aioutlet.product.created.v1",
        correlation_id="test-correlation-123"
    )
    
    if success:
        print("[SUCCESS] Event published successfully!")
        print("Check your RabbitMQ management console at http://localhost:15672")
        print("Look for exchange 'product.created' and messages")
    else:
        print("[FAILED] Failed to publish event")
        print("Make sure:")
        print("  1. Dapr sidecar is running (dapr run --app-id product-service)")
        print("  2. RabbitMQ is running (docker ps | grep rabbitmq)")
        print("  3. Dapr components are configured correctly")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(test_publish())
    sys.exit(0 if result else 1)
