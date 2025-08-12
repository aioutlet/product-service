"""
Frontend Aggregation Example

This example demonstrates how the frontend/API Gateway can aggregate
product data from product-service and inventory data from inventory-service.
"""

import asyncio
import httpx
from typing import List, Dict, Optional

class ProductServiceClient:
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip("/")
    
    async def get_product(self, product_id: str) -> Optional[Dict]:
        """Get product information."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/products/{product_id}")
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Error fetching product {product_id}: {e}")
                return None
    
    async def get_products(self, limit: int = 10) -> List[Dict]:
        """Get multiple products."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/products?limit={limit}")
                if response.status_code == 200:
                    return response.json()
                return []
            except Exception as e:
                print(f"Error fetching products: {e}")
                return []

class InventoryServiceClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
    
    async def get_inventory_by_sku(self, sku: str) -> Optional[Dict]:
        """Get inventory information by SKU."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/inventory/sku/{sku}")
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Error fetching inventory for SKU {sku}: {e}")
                return None
    
    async def check_stock(self, items: List[Dict]) -> Dict:
        """Check stock availability for multiple items."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/stock/check",
                    json={"items": items}
                )
                if response.status_code == 200:
                    return response.json()
                return {"available": False, "items": []}
            except Exception as e:
                print(f"Error checking stock: {e}")
                return {"available": False, "items": []}

class ProductAggregationService:
    """
    Service that aggregates product and inventory data.
    This demonstrates the Frontend Aggregation pattern.
    """
    
    def __init__(self):
        self.product_client = ProductServiceClient()
        self.inventory_client = InventoryServiceClient()
    
    async def get_product_with_inventory(self, product_id: str) -> Optional[Dict]:
        """
        Get a product with its inventory information.
        
        Args:
            product_id: Product ID
            
        Returns:
            Combined product and inventory data
        """
        # Get product data
        product = await self.product_client.get_product(product_id)
        if not product:
            return None
        
        # Get inventory data if product has SKU
        inventory = None
        if product.get("sku"):
            inventory = await self.inventory_client.get_inventory_by_sku(product["sku"])
        
        # Combine the data
        return {
            "product": product,
            "inventory": inventory,
            "in_stock": inventory["quantity_available"] > 0 if inventory else False,
            "available_quantity": inventory["quantity_available"] if inventory else 0
        }
    
    async def get_products_with_inventory(self, limit: int = 10) -> List[Dict]:
        """
        Get multiple products with their inventory information.
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of products with inventory data
        """
        # Get products
        products = await self.product_client.get_products(limit)
        if not products:
            return []
        
        # Get inventory data for products with SKUs
        results = []
        for product in products:
            inventory = None
            if product.get("sku"):
                inventory = await self.inventory_client.get_inventory_by_sku(product["sku"])
            
            results.append({
                "product": product,
                "inventory": inventory,
                "in_stock": inventory["quantity_available"] > 0 if inventory else False,
                "available_quantity": inventory["quantity_available"] if inventory else 0
            })
        
        return results
    
    async def check_order_availability(self, order_items: List[Dict]) -> Dict:
        """
        Check if all items in an order are available.
        
        Args:
            order_items: List of items with product_id and quantity
            
        Returns:
            Order availability information
        """
        # Get product information for each item to get SKUs
        stock_check_items = []
        product_map = {}
        
        for item in order_items:
            product = await self.product_client.get_product(item["product_id"])
            if product and product.get("sku"):
                stock_check_items.append({
                    "sku": product["sku"],
                    "quantity": item["quantity"]
                })
                product_map[product["sku"]] = product
        
        # Check stock availability
        if not stock_check_items:
            return {"available": False, "reason": "No valid products found"}
        
        stock_result = await self.inventory_client.check_stock(stock_check_items)
        
        return {
            "available": stock_result["available"],
            "items": stock_result["items"],
            "products": product_map
        }

async def example_usage():
    """Example of how to use the aggregation service."""
    aggregator = ProductAggregationService()
    
    print("🔍 Frontend Aggregation Example")
    print("=" * 40)
    
    # Example 1: Get single product with inventory
    print("\n1. Getting product with inventory:")
    product_with_inventory = await aggregator.get_product_with_inventory("some-product-id")
    if product_with_inventory:
        product = product_with_inventory["product"]
        print(f"   Product: {product['name']} - ${product['price']}")
        print(f"   In Stock: {product_with_inventory['in_stock']}")
        print(f"   Available: {product_with_inventory['available_quantity']} units")
    else:
        print("   Product not found")
    
    # Example 2: Get multiple products with inventory
    print("\n2. Getting products with inventory:")
    products_with_inventory = await aggregator.get_products_with_inventory(5)
    for item in products_with_inventory[:3]:  # Show first 3
        product = item["product"]
        print(f"   {product['name']}: {item['available_quantity']} available")
    
    # Example 3: Check order availability
    print("\n3. Checking order availability:")
    order_items = [
        {"product_id": "product-1", "quantity": 2},
        {"product_id": "product-2", "quantity": 1}
    ]
    availability = await aggregator.check_order_availability(order_items)
    print(f"   Order available: {availability['available']}")
    
    print("\n✅ Frontend aggregation example completed!")

if __name__ == "__main__":
    print("This is an example of how to aggregate product and inventory data")
    print("Run with: python scripts/frontend_aggregation_example.py")
    # Uncomment to run the example:
    # asyncio.run(example_usage())
