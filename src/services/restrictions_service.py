"""
Restrictions Service

Business logic for managing product restrictions and compliance metadata.
"""

from typing import Optional
from datetime import datetime, timezone

from src.repositories.product_repository import ProductRepository
from src.models.restrictions import (
    ProductRestrictions,
    UpdateProductRestrictionsRequest,
    ProductRestrictionsResponse
)
from src.services.dapr_publisher import get_dapr_publisher
from src.core.errors import ErrorResponse
from src.core.logger import logger


class RestrictionsService:
    """Service for managing product restrictions and compliance"""
    
    def __init__(self, repository: ProductRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Product repository instance
        """
        self.repository = repository
    
    async def update_restrictions(
        self,
        product_id: str,
        restrictions: ProductRestrictions,
        updated_by: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> ProductRestrictionsResponse:
        """
        Update product restrictions and compliance metadata.
        
        Args:
            product_id: Product ID
            restrictions: New restrictions configuration
            updated_by: User ID who updated restrictions
            correlation_id: Request correlation ID
            
        Returns:
            ProductRestrictionsResponse with updated data
            
        Raises:
            ErrorResponse: If product not found or validation fails
        """
        logger.info(
            f"Updating restrictions for product {product_id}",
            metadata={
                "product_id": product_id,
                "correlation_id": correlation_id
            }
        )
        
        # Get existing product
        product = await self.repository.find_by_id(product_id, correlation_id)
        if not product:
            raise ErrorResponse(
                f"Product {product_id} not found",
                status_code=404
            )
        
        # Update restrictions
        update_data = {
            "restrictions": restrictions.model_dump(),
            "updated_by": updated_by,
            "updated_at": datetime.now(timezone.utc)
        }
        
        updated_product = await self.repository.update(
            product_id,
            update_data,
            correlation_id
        )
        
        if not updated_product:
            raise ErrorResponse(
                f"Failed to update restrictions for product {product_id}",
                status_code=500
            )
        
        logger.info(
            f"Restrictions updated for product {product_id}",
            metadata={
                "product_id": product_id,
                "correlation_id": correlation_id
            }
        )
        
        # Publish restrictions.updated event
        try:
            publisher = get_dapr_publisher()
            await publisher.publish(
                topic="product.restrictions.updated",
                data={
                    "productId": product_id,
                    "sku": product.get("sku"),
                    "restrictions": restrictions.model_dump(),
                    "updatedBy": updated_by,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "restrictions_updated"
                },
                event_type="com.aioutlet.product.restrictions.updated.v1",
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error(
                f"Failed to publish restrictions.updated event: {str(e)}",
                metadata={"product_id": product_id}
            )
        
        return ProductRestrictionsResponse(
            product_id=product_id,
            sku=product.get("sku"),
            restrictions=ProductRestrictions(**updated_product.get("restrictions", {})),
            updated_at=updated_product.get("updated_at"),
            updated_by=updated_by
        )
    
    async def get_restrictions(
        self,
        product_id: str,
        correlation_id: Optional[str] = None
    ) -> ProductRestrictionsResponse:
        """
        Get product restrictions and compliance metadata.
        
        Args:
            product_id: Product ID
            correlation_id: Request correlation ID
            
        Returns:
            ProductRestrictionsResponse
            
        Raises:
            ErrorResponse: If product not found
        """
        product = await self.repository.find_by_id(product_id, correlation_id)
        if not product:
            raise ErrorResponse(
                f"Product {product_id} not found",
                status_code=404
            )
        
        restrictions_data = product.get("restrictions", {})
        
        # Handle legacy restrictions format
        if not restrictions_data or "age_restriction" not in restrictions_data:
            # Convert legacy format if exists
            if product.get("restrictions"):
                legacy = product["restrictions"]
                restrictions_data = {
                    "age_restriction": "18+" if legacy.get("age_restricted") else "none",
                    "shipping_restrictions": [
                        {"type": "hazmat", "reason": "Hazardous material"}
                    ] if legacy.get("hazardous_material") else []
                }
            else:
                restrictions_data = {"age_restriction": "none"}
        
        return ProductRestrictionsResponse(
            product_id=product_id,
            sku=product.get("sku"),
            restrictions=ProductRestrictions(**restrictions_data),
            updated_at=product.get("updated_at"),
            updated_by=product.get("updated_by")
        )
    
    async def check_age_eligibility(
        self,
        product_id: str,
        customer_age: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Check if customer meets age requirements for product.
        
        Args:
            product_id: Product ID
            customer_age: Customer's age (None if unknown)
            correlation_id: Request correlation ID
            
        Returns:
            True if eligible, False otherwise
            
        Raises:
            ErrorResponse: If product not found
        """
        restrictions_response = await self.get_restrictions(product_id, correlation_id)
        restrictions = restrictions_response.restrictions
        
        # If no age known and product is age-restricted, deny access
        if customer_age is None and restrictions.age_restriction != "none":
            return False
        
        # Check age restrictions
        if restrictions.age_restriction == "none":
            return True
        elif restrictions.age_restriction == "18+":
            return customer_age >= 18
        elif restrictions.age_restriction == "21+":
            return customer_age >= 21
        elif restrictions.age_restriction == "custom":
            return customer_age >= restrictions.custom_age_limit
        
        return True
    
    async def check_regional_availability(
        self,
        product_id: str,
        country_code: str,
        state_code: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Check if product is available in specified region.
        
        Args:
            product_id: Product ID
            country_code: ISO 3166-1 alpha-2 country code
            state_code: State/province code (if applicable)
            correlation_id: Request correlation ID
            
        Returns:
            True if available, False otherwise
            
        Raises:
            ErrorResponse: If product not found
        """
        restrictions_response = await self.get_restrictions(product_id, correlation_id)
        restrictions = restrictions_response.restrictions
        
        if not restrictions.regional_availability:
            return True  # No restrictions = available everywhere
        
        regional = restrictions.regional_availability
        
        # Check country-level restrictions
        if regional.restricted_countries and country_code in regional.restricted_countries:
            return False
        
        if regional.available_countries and country_code not in regional.available_countries:
            return False
        
        # Check state-level restrictions if state provided
        if state_code:
            if regional.restricted_states:
                restricted_states_for_country = regional.restricted_states.get(country_code, [])
                if state_code in restricted_states_for_country:
                    return False
            
            if regional.available_states:
                available_states_for_country = regional.available_states.get(country_code, [])
                if available_states_for_country and state_code not in available_states_for_country:
                    return False
        
        return True
    
    async def get_applicable_shipping_restrictions(
        self,
        product_id: str,
        correlation_id: Optional[str] = None
    ) -> list:
        """
        Get list of shipping restrictions for a product.
        
        Args:
            product_id: Product ID
            correlation_id: Request correlation ID
            
        Returns:
            List of shipping restrictions
            
        Raises:
            ErrorResponse: If product not found
        """
        restrictions_response = await self.get_restrictions(product_id, correlation_id)
        restrictions = restrictions_response.restrictions
        
        return restrictions.shipping_restrictions or []
