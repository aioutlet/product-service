"""
Dapr Service Invocation Client

Replaces custom ServiceClient with Dapr's service invocation building block.
Provides automatic service discovery, load balancing, retries, and observability.
"""

import os
import logging
from typing import Any, Dict, Optional, Union

import aiohttp
from src.utils.correlation_id import get_correlation_id

logger = logging.getLogger(__name__)


class DaprServiceClient:
    """Dapr service invocation client for inter-service communication"""
    
    def __init__(self):
        self.dapr_port = os.getenv('DAPR_HTTP_PORT', '3500')
        self.base_url = f"http://localhost:{self.dapr_port}"
        
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Create headers with correlation ID and Dapr headers"""
        headers = {
            "Content-Type": "application/json",
            "dapr-app-id": os.getenv('DAPR_APP_ID', 'product-service')
        }
        
        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["x-correlation-id"] = correlation_id
            
        # Add any additional headers
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    async def invoke_service(
        self,
        app_id: str,
        method_name: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        http_verb: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Invoke a method on another service via Dapr
        
        Args:
            app_id: Target service's Dapr app ID
            method_name: HTTP endpoint (e.g., "api/users/123")
            data: Request payload for POST/PUT requests
            http_verb: HTTP method (GET, POST, PUT, DELETE)
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
        """
        try:
            # Construct Dapr service invocation URL
            url = f"{self.base_url}/v1.0/invoke/{app_id}/method/{method_name}"
            
            # Prepare headers
            request_headers = self._get_headers(headers)
            
            # Log the service invocation
            logger.info(
                f"Invoking service via Dapr: {app_id}/{method_name}",
                extra={
                    "app_id": app_id,
                    "method": method_name,
                    "http_verb": http_verb,
                    "correlation_id": request_headers.get("x-correlation-id")
                }
            )
            
            async with aiohttp.ClientSession() as session:
                # Choose the appropriate HTTP method
                if http_verb.upper() == "GET":
                    async with session.get(
                        url,
                        headers=request_headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        return await self._handle_response(response, app_id, method_name)
                        
                elif http_verb.upper() == "POST":
                    async with session.post(
                        url,
                        json=data if isinstance(data, dict) else None,
                        data=data if isinstance(data, str) else None,
                        headers=request_headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        return await self._handle_response(response, app_id, method_name)
                        
                elif http_verb.upper() == "PUT":
                    async with session.put(
                        url,
                        json=data if isinstance(data, dict) else None,
                        data=data if isinstance(data, str) else None,
                        headers=request_headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        return await self._handle_response(response, app_id, method_name)
                        
                elif http_verb.upper() == "DELETE":
                    async with session.delete(
                        url,
                        headers=request_headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        return await self._handle_response(response, app_id, method_name)
                        
                else:
                    raise ValueError(f"Unsupported HTTP method: {http_verb}")
                    
        except Exception as e:
            logger.error(
                f"Failed to invoke service {app_id}/{method_name}: {str(e)}",
                extra={
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise
    
    async def _handle_response(self, response: aiohttp.ClientResponse, app_id: str, method_name: str) -> Dict[str, Any]:
        """Handle the response from Dapr service invocation"""
        try:
            if response.status >= 400:
                error_text = await response.text()
                logger.error(
                    f"Service invocation failed: {app_id}/{method_name}",
                    extra={
                        "app_id": app_id,
                        "method": method_name,
                        "status_code": response.status,
                        "error": error_text
                    }
                )
                raise Exception(f"Service {app_id} returned {response.status}: {error_text}")
            
            # Try to parse JSON response
            try:
                return await response.json()
            except:
                # If not JSON, return text
                text = await response.text()
                return {"data": text, "content_type": response.content_type}
                
        except Exception as e:
            logger.error(f"Error handling response from {app_id}/{method_name}: {str(e)}")
            raise

    # Convenience methods for common service calls
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user from user-service"""
        return await self.invoke_service(
            app_id="user-service",
            method_name=f"api/users/{user_id}",
            http_verb="GET"
        )
    
    async def check_inventory(self, product_id: str) -> Dict[str, Any]:
        """Check inventory from inventory-service"""
        return await self.invoke_service(
            app_id="inventory-service", 
            method_name=f"api/inventory/{product_id}",
            http_verb="GET"
        )
    
    async def validate_auth(self, token: str) -> Dict[str, Any]:
        """Validate auth token with auth-service"""
        return await self.invoke_service(
            app_id="auth-service",
            method_name="api/auth/validate",
            http_verb="POST",
            data={"token": token}
        )
    
    async def notify_order_service(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notify order-service of product changes"""
        return await self.invoke_service(
            app_id="order-service",
            method_name="api/orders/product-updated",
            http_verb="POST",
            data=order_data
        )

    async def health_check(self) -> bool:
        """Check if Dapr sidecar is available"""
        try:
            url = f"{self.base_url}/v1.0/healthz"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    return response.status == 200
        except Exception:
            return False


# Global instance
_dapr_client: Optional[DaprServiceClient] = None


def get_dapr_service_client() -> DaprServiceClient:
    """Get the global Dapr service client instance"""
    global _dapr_client
    if _dapr_client is None:
        _dapr_client = DaprServiceClient()
    return _dapr_client


# Backward compatibility helpers (can be removed once all code is migrated)
async def call_user_service(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Legacy compatibility for user service calls"""
    client = get_dapr_service_client()
    return await client.invoke_service("user-service", endpoint.lstrip("/"), data, method)

async def call_inventory_service(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Legacy compatibility for inventory service calls"""
    client = get_dapr_service_client()
    return await client.invoke_service("inventory-service", endpoint.lstrip("/"), data, method)