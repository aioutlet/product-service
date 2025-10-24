"""
Service Communication Helper with Correlation ID for Python FastAPI services
Use this for making HTTP requests between microservices
with proper correlation ID propagation
"""

import os
from typing import Any, Dict, Optional

import httpx

from src.utils.correlation_id import (
    create_headers_with_correlation_id,
)


class ServiceClient:
    """HTTP client for inter-service communication with correlation ID support"""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout

    def _get_headers(
        self, additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Create headers with correlation ID"""
        headers = create_headers_with_correlation_id(additional_headers)
        return headers

    async def get(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> httpx.Response:
        """Make a GET request with correlation ID"""
        request_headers = self._get_headers(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}", headers=request_headers, **kwargs
            )
            return response

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make a POST request with correlation ID"""
        request_headers = self._get_headers(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=request_headers,
                **kwargs,
            )
            return response

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make a PUT request with correlation ID"""
        request_headers = self._get_headers(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=request_headers,
                **kwargs,
            )
            return response

    async def delete(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> httpx.Response:
        """Make a DELETE request with correlation ID"""
        request_headers = self._get_headers(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}{endpoint}", headers=request_headers, **kwargs
            )
            return response


# Pre-configured service clients
user_service_client = ServiceClient(
    os.getenv("USER_SERVICE_URL", "http://localhost:5000")
)
auth_service_client = ServiceClient(
    os.getenv("AUTH_SERVICE_URL", "http://localhost:4000")
)
inventory_service_client = ServiceClient(
    os.getenv("INVENTORY_SERVICE_URL", "http://localhost:3000")
)
order_service_client = ServiceClient(
    os.getenv("ORDER_SERVICE_URL", "http://localhost:7000")
)
payment_service_client = ServiceClient(
    os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8080")
)
admin_service_client = ServiceClient(
    os.getenv("ADMIN_SERVICE_URL", "http://localhost:6000")
)


async def log_with_correlation_id(
    level: str, message: str, extra: Optional[Dict[str, Any]] = None
):
    """Log a message with correlation ID"""
    correlation_id = get_correlation_id()
    log_data = {"correlation_id": correlation_id, "message": message}

    if extra:
        log_data.update(extra)

    print(f"[{correlation_id}] {level.upper()}: {message}", log_data)
