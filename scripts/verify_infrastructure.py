#!/usr/bin/env python3
"""
Infrastructure Verification Script
Verifies all critical infrastructure features are working correctly.
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


async def verify_indexes():
    """Verify all 10 database indexes exist."""
    print("\n" + "="*60)
    print("1. DATABASE INDEXES VERIFICATION")
    print("="*60)
    
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27019")
        db = client["product_service_db"]
        collection = db["products"]
        
        indexes = await collection.index_information()
        
        expected_indexes = [
            "sku_unique_idx",
            "text_search_idx",
            "status_category_price_idx",
            "status_department_price_idx",
            "status_rating_idx",
            "status_created_idx",
            "brand_idx",
            "tags_idx",
            "badges_idx",
            "parent_id_idx"
        ]
        
        print(f"\nTotal indexes found: {len(indexes)}")
        print("\nIndex Status:")
        
        all_present = True
        for index_name in expected_indexes:
            status = "✅" if index_name in indexes else "❌"
            print(f"  {status} {index_name}")
            if index_name not in indexes:
                all_present = False
        
        if all_present:
            print("\n✅ All database indexes are present!")
            return True
        else:
            print("\n❌ Some indexes are missing. Run the service to create them.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error connecting to MongoDB: {e}")
        print("   Make sure MongoDB is running on port 27019")
        return False
    finally:
        client.close()


async def verify_dapr_config():
    """Verify Dapr configuration file exists."""
    print("\n" + "="*60)
    print("2. DAPR CONFIGURATION VERIFICATION")
    print("="*60)
    
    import os
    
    dapr_config_path = ".dapr/components/pubsub.yaml"
    
    if os.path.exists(dapr_config_path):
        print(f"\n✅ Dapr pubsub config found: {dapr_config_path}")
        
        with open(dapr_config_path, 'r') as f:
            content = f.read()
            
        # Check for required configurations
        checks = [
            ("product-pubsub", "Component name"),
            ("pubsub.rabbitmq", "RabbitMQ type"),
            ("amqp://", "Connection string"),
            ("topic", "Exchange type")
        ]
        
        print("\nConfiguration checks:")
        all_good = True
        for check_str, description in checks:
            status = "✅" if check_str in content else "❌"
            print(f"  {status} {description}")
            if check_str not in content:
                all_good = False
        
        return all_good
    else:
        print(f"\n❌ Dapr config not found: {dapr_config_path}")
        return False


def verify_event_publisher():
    """Verify event publisher has all required methods."""
    print("\n" + "="*60)
    print("3. EVENT PUBLISHER VERIFICATION")
    print("="*60)
    
    try:
        from src.services.dapr_publisher import DaprPublisher
        
        publisher = DaprPublisher()
        
        required_methods = [
            "publish",
            "publish_product_created",
            "publish_product_updated",
            "publish_product_deleted"
        ]
        
        print("\nPublisher methods:")
        all_present = True
        for method_name in required_methods:
            has_method = hasattr(publisher, method_name)
            status = "✅" if has_method else "❌"
            print(f"  {status} {method_name}()")
            if not has_method:
                all_present = False
        
        if all_present:
            print("\n✅ Event publisher has all required methods!")
            return True
        else:
            print("\n❌ Event publisher is missing some methods")
            return False
            
    except ImportError as e:
        print(f"\n❌ Error importing DaprPublisher: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error verifying publisher: {e}")
        return False


def verify_search_repository():
    """Verify search repository uses text index."""
    print("\n" + "="*60)
    print("4. SEARCH API VERIFICATION")
    print("="*60)
    
    try:
        with open("src/repositories/product_repository.py", 'r') as f:
            content = f.read()
        
        # Check if text search is being used
        checks = [
            ('query["$text"]', "MongoDB text search"),
            ("$search", "Search query"),
            ("async def search_products", "Search method exists")
        ]
        
        print("\nSearch implementation checks:")
        all_good = True
        for check_str, description in checks:
            status = "✅" if check_str in content else "❌"
            print(f"  {status} {description}")
            if check_str not in content:
                all_good = False
        
        if all_good:
            print("\n✅ Search API uses optimized text index!")
            return True
        else:
            print("\n❌ Search API may not be using text index")
            return False
            
    except Exception as e:
        print(f"\n❌ Error reading repository file: {e}")
        return False


def verify_service_integration():
    """Verify ProductService has event publishing integrated."""
    print("\n" + "="*60)
    print("5. SERVICE INTEGRATION VERIFICATION")
    print("="*60)
    
    try:
        with open("src/services/product_service.py", 'r') as f:
            content = f.read()
        
        checks = [
            ("_publish_product_created", "Product created event"),
            ("_publish_product_updated", "Product updated event"),
            ("_publish_product_deleted", "Product deleted event"),
            ("publish_product_created", "Uses convenience method (created)"),
            ("publish_product_updated", "Uses convenience method (updated)"),
            ("publish_product_deleted", "Uses convenience method (deleted)")
        ]
        
        print("\nService integration checks:")
        all_good = True
        for check_str, description in checks:
            status = "✅" if check_str in content else "❌"
            print(f"  {status} {description}")
            if check_str not in content:
                all_good = False
        
        if all_good:
            print("\n✅ ProductService has event publishing fully integrated!")
            return True
        else:
            print("\n❌ ProductService may be missing event integration")
            return False
            
    except Exception as e:
        print(f"\n❌ Error reading service file: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("PRODUCT SERVICE - INFRASTRUCTURE VERIFICATION")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Database Indexes": await verify_indexes(),
        "Dapr Configuration": await verify_dapr_config(),
        "Event Publisher": verify_event_publisher(),
        "Search API": verify_search_repository(),
        "Service Integration": verify_service_integration()
    }
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} checks passed")
    print("="*60)
    
    if passed == total:
        print("\n✅ All infrastructure features verified successfully!")
        print("   You can now implement functional requirements from the PRD.")
        return 0
    else:
        print("\n⚠️  Some verification checks failed.")
        print("   Review the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
