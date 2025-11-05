#!/usr/bin/env python3
"""
Simple test script to verify Dapr integration
"""

import asyncio
import json
import os
import sys

import aiohttp


async def test_dapr_health():
    """Test if Dapr sidecar is healthy"""
    dapr_port = os.getenv('DAPR_HTTP_PORT', '3500')
    url = f"http://localhost:{dapr_port}/v1.0/healthz"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    print("✅ Dapr sidecar is healthy")
                    return True
                else:
                    print(f"❌ Dapr sidecar returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Dapr sidecar is not reachable: {e}")
        return False


async def test_dapr_pubsub():
    """Test Dapr pub/sub functionality"""
    dapr_port = os.getenv('DAPR_HTTP_PORT', '3500')
    pubsub_name = os.getenv('DAPR_PUBSUB_NAME', 'product-pubsub')
    
    url = f"http://localhost:{dapr_port}/v1.0/publish/{pubsub_name}/test-topic"
    
    test_event = {
        "specversion": "1.0",
        "type": "test.event",
        "source": "/test",
        "id": "test-123",
        "data": {"message": "Hello from Product Service!"}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=test_event,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as response:
                if response.status == 204:
                    print("✅ Successfully published test event to Dapr")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to publish test event: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Error testing Dapr pub/sub: {e}")
        return False


async def test_product_service():
    """Test if Product Service is running"""
    app_port = os.getenv('DAPR_APP_PORT', '8003')
    url = f"http://localhost:{app_port}/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ Product Service is healthy")
                    print(f"   Service: {health_data.get('service', 'N/A')}")
                    print(f"   Status: {health_data.get('status', 'N/A')}")
                    return True
                else:
                    print(f"❌ Product Service returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Product Service is not reachable: {e}")
        return False


async def test_dapr_publisher():
    """Test our Dapr publisher service"""
    try:
        # Import our Dapr publisher
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.services.dapr_publisher import get_dapr_publisher
        
        publisher = get_dapr_publisher()
        
        # Test health check
        if await publisher.health_check():
            print("✅ Dapr Publisher health check passed")
        else:
            print("❌ Dapr Publisher health check failed")
            return False
        
        # Test event publishing
        test_product_data = {
            "_id": "test-product-123",
            "name": "Test Product",
            "price": 29.99,
            "created_at": "2025-11-05T10:00:00Z"
        }
        
        success = await publisher.publish_product_created(test_product_data, "test-correlation-123")
        if success:
            print("✅ Successfully published test product.created event")
            return True
        else:
            print("❌ Failed to publish test product.created event")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Dapr publisher: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing Dapr Integration for Product Service")
    print("=" * 50)
    
    tests = [
        ("Product Service Health", test_product_service),
        ("Dapr Sidecar Health", test_dapr_health),
        ("Dapr Pub/Sub", test_dapr_pubsub),
        ("Dapr Publisher Service", test_dapr_publisher)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nSummary: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Dapr integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)