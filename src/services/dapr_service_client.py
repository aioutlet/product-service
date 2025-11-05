"""
Dapr Service Invocation Client

This module provides a client to invoke other microservices using Dapr service invocation.
Dapr handles service discovery, retries, circuit breaking, and distributed tracing automatically.
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from src.core.logger import logger


class DaprServiceClient:
    """
    Client for invoking microservices through Dapr sidecar.
    
    Dapr Service Invocation provides:
    - Service discovery (no need to know exact URLs)
    - Automatic retries and circuit breaking
    - Distributed tracing propagation
    - mTLS for secure service-to-service communication
    - Load balancing
    
    Endpoint format: http://localhost:{dapr-http-port}/v1.0/invoke/{app-id}/method/{method-name}
    """

    def __init__(self, dapr_http_port: str = None):
        """
        Initialize the Dapr service invocation client.

        Args:
            dapr_http_port: Dapr sidecar HTTP port (default: from env or 3500)
        """
        self.dapr_http_port = dapr_http_port or os.getenv('DAPR_HTTP_PORT', '3500')
        self.dapr_url = f"http://localhost:{self.dapr_http_port}"
        self.client = httpx.AsyncClient(timeout=30.0)

    def _build_invoke_url(self, app_id: str, method: str) -> str:
        """
        Build Dapr service invocation URL.
        
        Args:
            app_id: Target service's Dapr app ID
            method: API method path (e.g., 'inventory/sku/ABC123')
            
        Returns:
            Full Dapr invocation URL
        """
        # Remove leading slash if present
        method = method.lstrip('/')
        return f"{self.dapr_url}/v1.0/invoke/{app_id}/method/{method}"

    async def invoke_get(
        self, 
        app_id: str, 
        method: str, 
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None
    ) -> Any:
        """
        Invoke GET method on another service via Dapr.
        
        Args:
            app_id: Target service's Dapr app ID (e.g., 'inventory-service')
            method: API method path (e.g., 'inventory/sku/ABC123')
            headers: Optional HTTP headers
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = self._build_invoke_url(app_id, method)
        
        request_headers = headers or {}
        if correlation_id:
            request_headers['X-Correlation-ID'] = correlation_id
        
        try:
            logger.debug(
                f"Dapr service invocation: GET {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "correlationId": correlation_id
                }
            )
            
            response = await self.client.get(url, headers=request_headers)
            response.raise_for_status()
            
            logger.debug(
                f"Dapr service invocation successful: {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "statusCode": response.status_code
                }
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Resource not found: {app_id}/{method}")
                return None
            logger.error(
                f"Dapr service invocation failed: {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "statusCode": e.response.status_code,
                    "error": str(e)
                }
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Dapr service invocation error: {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "error": str(e)
                }
            )
            raise

    async def invoke_post(
        self, 
        app_id: str, 
        method: str, 
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None
    ) -> Any:
        """
        Invoke POST method on another service via Dapr.
        
        Args:
            app_id: Target service's Dapr app ID
            method: API method path
            data: Request body (will be JSON-encoded)
            headers: Optional HTTP headers
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = self._build_invoke_url(app_id, method)
        
        request_headers = headers or {}
        request_headers['Content-Type'] = 'application/json'
        if correlation_id:
            request_headers['X-Correlation-ID'] = correlation_id
        
        try:
            logger.debug(
                f"Dapr service invocation: POST {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "correlationId": correlation_id
                }
            )
            
            response = await self.client.post(url, json=data, headers=request_headers)
            response.raise_for_status()
            
            logger.debug(
                f"Dapr service invocation successful: {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "statusCode": response.status_code
                }
            )
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(
                f"Dapr service invocation error: {app_id}/{method}",
                metadata={
                    "appId": app_id,
                    "method": method,
                    "error": str(e)
                }
            )
            raise

    async def invoke_put(
        self, 
        app_id: str, 
        method: str, 
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None
    ) -> Any:
        """
        Invoke PUT method on another service via Dapr.
        
        Args:
            app_id: Target service's Dapr app ID
            method: API method path
            data: Request body (will be JSON-encoded)
            headers: Optional HTTP headers
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = self._build_invoke_url(app_id, method)
        
        request_headers = headers or {}
        request_headers['Content-Type'] = 'application/json'
        if correlation_id:
            request_headers['X-Correlation-ID'] = correlation_id
        
        try:
            response = await self.client.put(url, json=data, headers=request_headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Dapr PUT invocation error: {app_id}/{method} - {str(e)}")
            raise

    async def invoke_delete(
        self, 
        app_id: str, 
        method: str,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None
    ) -> Any:
        """
        Invoke DELETE method on another service via Dapr.
        
        Args:
            app_id: Target service's Dapr app ID
            method: API method path
            headers: Optional HTTP headers
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Response JSON data or None
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = self._build_invoke_url(app_id, method)
        
        request_headers = headers or {}
        if correlation_id:
            request_headers['X-Correlation-ID'] = correlation_id
        
        try:
            response = await self.client.delete(url, headers=request_headers)
            response.raise_for_status()
            
            # DELETE might return no content
            if response.status_code == 204:
                return None
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Dapr DELETE invocation error: {app_id}/{method} - {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global client instance
_dapr_client: Optional[DaprServiceClient] = None


def get_dapr_client() -> DaprServiceClient:
    """
    Get the global Dapr service invocation client instance.

    Returns:
        DaprServiceClient: The client instance
    """
    global _dapr_client
    if _dapr_client is None:
        _dapr_client = DaprServiceClient()
    return _dapr_client


async def close_dapr_client():
    """Close the global Dapr client."""
    global _dapr_client
    if _dapr_client:
        await _dapr_client.close()
        _dapr_client = None
