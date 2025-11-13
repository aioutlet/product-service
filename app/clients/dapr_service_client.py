"""
Dapr Service Invocation Client
Provides inter-service communication using Dapr's service invocation building block.
Includes automatic service discovery, load balancing, retries, and observability.
Automatically detects Dapr availability and falls back to direct HTTP calls when needed.
"""

from typing import Any, Dict, Optional, Union
import os

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from app.core.logger import logger
from app.core.config import config
from app.middleware.trace_context import get_trace_id


# Service URL mappings for direct HTTP fallback
SERVICE_URLS = {
    "inventory-service": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:5002")
}


class DaprServiceClient:
    """
    Dapr service invocation client for inter-service communication.
    Uses Dapr's service invocation building block for resilient service calls.
    Automatically falls back to direct HTTP when Dapr is unavailable.
    """
    
    def __init__(self):
        self.dapr_http_port = config.dapr_http_port
        self.base_url = f"http://localhost:{self.dapr_http_port}"
        self.service_name = config.service_name
        self._dapr_available: Optional[bool] = None
        
        logger.info(
            "Dapr service client initialized",
            metadata={
                "event": "dapr_client_init",
                "dapr_port": self.dapr_http_port,
                "base_url": self.base_url
            }
        )
    
    async def _check_dapr_availability(self) -> bool:
        """
        Check if Dapr sidecar is available by calling the health endpoint.
        Caches the result to avoid repeated health checks.
        
        Returns:
            True if Dapr is available, False otherwise
        """
        if self._dapr_available is not None:
            return self._dapr_available
            
        if not AIOHTTP_AVAILABLE:
            self._dapr_available = False
            return False
            
        try:
            url = f"{self.base_url}/v1.0/healthz"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=0.5)) as response:
                    self._dapr_available = response.status == 204
                    
                    logger.info(
                        f"Dapr availability check: {'available' if self._dapr_available else 'unavailable'}",
                        metadata={
                            "event": "dapr_availability_check",
                            "available": self._dapr_available,
    async def invoke_service(
        self,
        app_id: str,
        method_name: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        http_verb: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Invoke a method on another service via Dapr or direct HTTP.
        Automatically detects Dapr availability and falls back to direct HTTP.
        
        Args:
            app_id: Target service's Dapr app ID (e.g., 'inventory-service')
            method_name: HTTP endpoint path (e.g., 'api/inventory/check')
            data: Request payload for POST/PUT requests
            http_verb: HTTP method (GET, POST, PUT, DELETE, PATCH)
            headers: Additional headers to include
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If service invocation fails
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for service invocation")
        
        # Check if Dapr is available
        dapr_available = await self._check_dapr_availability()
        
        if dapr_available:
            return await self._invoke_dapr_service(app_id, method_name, data, http_verb, headers, timeout)
        else:
            return await self._invoke_direct_http(app_id, method_name, data, http_verb, headers, timeout)
    
    async def _invoke_dapr_service(
        self,
        app_id: str,
        method_name: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        http_verb: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Invoke a method on another service via Dapr service invocation.
        
        Args:
            app_id: Target service's Dapr app ID
            method_name: HTTP endpoint path
            data: Request payload
            http_verb: HTTP method
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
        """
        try:
        # Add trace ID for distributed tracing
        trace_id = get_trace_id()
        if trace_id:
            headers["traceparent"] = f"00-{trace_id}-{trace_id[:16]}-01"
            
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
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Invoke a method on another service via Dapr service invocation.
        
        Args:
            app_id: Target service's Dapr app ID (e.g., 'inventory-service')
            method_name: HTTP endpoint path (e.g., 'api/inventory/check')
            data: Request payload for POST/PUT requests
            http_verb: HTTP method (GET, POST, PUT, DELETE, PATCH)
            headers: Additional headers to include
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If service invocation fails
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for Dapr service invocation")
        
        try:
            # Construct Dapr service invocation URL
            # Format: http://localhost:<dapr-http-port>/v1.0/invoke/<app-id>/method/<method-name>
            url = f"{self.base_url}/v1.0/invoke/{app_id}/method/{method_name}"
            
            # Prepare headers
            request_headers = self._get_headers(headers)
            
            # Log the service invocation
            logger.info(
                f"Invoking service via Dapr: {app_id}/{method_name}",
                metadata={
                    "event": "dapr_service_invocation",
                    "app_id": app_id,
                    "method": method_name,
                    "http_verb": http_verb,
                    "trace_id": request_headers.get("traceparent")
                }
            )
            
            async with aiohttp.ClientSession() as session:
            logger.error(
                f"Failed to invoke service {app_id}/{method_name}: {str(e)}",
                metadata={
                    "event": "dapr_invocation_error",
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise
    
    async def _invoke_direct_http(
        self,
        app_id: str,
        method_name: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        http_verb: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Invoke a method on another service via direct HTTP (fallback when Dapr unavailable).
        
        Args:
            app_id: Target service's app ID
            method_name: HTTP endpoint path
            data: Request payload
            http_verb: HTTP method
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
        """
        try:
            # Get service URL from mapping
            service_base_url = SERVICE_URLS.get(app_id)
            if not service_base_url:
                raise ValueError(
                    f"No direct URL configured for service '{app_id}'. "
                    f"Add {app_id.upper().replace('-', '_')}_URL to environment variables."
                )
            
            # Construct direct HTTP URL
            # Remove leading slash from method_name if present
            method_path = method_name.lstrip('/')
            url = f"{service_base_url}/{method_path}"
            
            # Prepare headers
            request_headers = self._get_headers(headers)
            
            # Log the direct service call
            logger.info(
                f"Invoking service via direct HTTP: {app_id}/{method_name}",
                metadata={
                    "event": "direct_http_invocation",
                    "app_id": app_id,
                    "method": method_name,
                    "http_verb": http_verb,
                    "url": url,
                    "trace_id": request_headers.get("traceparent")
                }
            )
            
            async with aiohttp.ClientSession() as session:
                http_method = http_verb.upper()
                
                request_kwargs = {
                    "headers": request_headers,
                    "timeout": aiohttp.ClientTimeout(total=timeout)
                }
                
                if http_method in ["POST", "PUT", "PATCH"] and data:
                    if isinstance(data, dict):
                        request_kwargs["json"] = data
                    else:
                        request_kwargs["data"] = data
                
                async with session.request(http_method, url, **request_kwargs) as response:
                    return await self._handle_response(response, app_id, method_name)
                    
        except aiohttp.ClientError as e:
            logger.error(
                f"Network error invoking service {app_id}/{method_name} via direct HTTP: {str(e)}",
                metadata={
                    "event": "direct_http_network_error",
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise Exception(f"Failed to connect to service {app_id}: {str(e)}")
            
        except Exception as e:
            logger.error(
                f"Failed to invoke service {app_id}/{method_name} via direct HTTP: {str(e)}",
                metadata={
                    "event": "direct_http_error",
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise
    
    async def _handle_response(_kwargs["json"] = data
                    else:
                        request_kwargs["data"] = data
                
                # Make the request
                async with session.request(http_method, url, **request_kwargs) as response:
                    return await self._handle_response(response, app_id, method_name)
                    
        except aiohttp.ClientError as e:
            logger.error(
                f"Network error invoking service {app_id}/{method_name}: {str(e)}",
                metadata={
                    "event": "dapr_invocation_network_error",
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise Exception(f"Failed to connect to service {app_id}: {str(e)}")
            
        except Exception as e:
            logger.error(
                f"Failed to invoke service {app_id}/{method_name}: {str(e)}",
                metadata={
                    "event": "dapr_invocation_error",
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise
    
    async def _handle_response(
        self,
        response: "aiohttp.ClientResponse",
        app_id: str,
        method_name: str
    ) -> Dict[str, Any]:
        """
        Handle the response from Dapr service invocation.
        
        Args:
            response: aiohttp response object
            app_id: Target service app ID
            method_name: Invoked method name
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If response indicates an error
        """
        try:
            # Check for HTTP errors
            if response.status >= 400:
                error_text = await response.text()
                logger.error(
                    f"Service invocation failed: {app_id}/{method_name}",
                    metadata={
                        "event": "dapr_invocation_http_error",
                        "app_id": app_id,
                        "method": method_name,
                        "status_code": response.status,
                        "error": error_text
                    }
                )
                raise Exception(f"Service {app_id} returned {response.status}: {error_text}")
            
            # Try to parse JSON response
            try:
                result = await response.json()
                logger.info(
                    f"Service invocation successful: {app_id}/{method_name}",
                    metadata={
                        "event": "dapr_invocation_success",
                        "app_id": app_id,
                        "method": method_name,
                        "status_code": response.status
                    }
                )
                return result
            except Exception:
                # If not JSON, return text wrapped in dict
                text = await response.text()
                return {
                    "data": text,
                    "content_type": str(response.content_type),
                    "status": response.status
                }
                
        except Exception as e:
            logger.error(
                f"Error handling response from {app_id}/{method_name}: {str(e)}",
                metadata={
                    "event": "dapr_response_error",
                    "app_id": app_id,
                    "method": method_name,
                    "error": str(e)
                }
            )
            raise

    # Convenience methods for common HTTP verbs
    async def get(self, app_id: str, method_name: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET request via Dapr service invocation"""
        return await self.invoke_service(app_id, method_name, http_verb="GET", headers=headers)
    
    async def post(
        self,
        app_id: str,
        method_name: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """POST request via Dapr service invocation"""
        return await self.invoke_service(app_id, method_name, data=data, http_verb="POST", headers=headers)
    
    async def put(
        self,
        app_id: str,
        method_name: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """PUT request via Dapr service invocation"""
        return await self.invoke_service(app_id, method_name, data=data, http_verb="PUT", headers=headers)
    
    async def delete(self, app_id: str, method_name: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """DELETE request via Dapr service invocation"""
        return await self.invoke_service(app_id, method_name, http_verb="DELETE", headers=headers)

    async def health_check(self) -> bool:
        """
        Check if Dapr sidecar is available and healthy.
        
        Returns:
            True if Dapr is healthy, False otherwise
        """
        if not AIOHTTP_AVAILABLE:
            return False
            
        try:
            url = f"{self.base_url}/v1.0/healthz"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    is_healthy = response.status == 200
                    logger.debug(
                        f"Dapr health check: {'healthy' if is_healthy else 'unhealthy'}",
                        metadata={
                            "event": "dapr_health_check",
                            "healthy": is_healthy,
                            "status": response.status
                        }
                    )
                    return is_healthy
        except Exception as e:
            logger.warning(
                f"Dapr health check failed: {str(e)}",
                metadata={"event": "dapr_health_check_error", "error": str(e)}
            )
            return False


# Global instance
_dapr_client: Optional[DaprServiceClient] = None


def get_dapr_service_client() -> DaprServiceClient:
    """
    Get the global Dapr service client instance.
    Creates a new instance if one doesn't exist.
    
    Returns:
        DaprServiceClient instance
    """
    global _dapr_client
    if _dapr_client is None:
        _dapr_client = DaprServiceClient()
    return _dapr_client
