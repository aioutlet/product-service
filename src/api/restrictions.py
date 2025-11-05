"""
Product Restrictions API Endpoints

Endpoints for managing product restrictions, compliance metadata,
age verification, and regional availability.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from src.models.restrictions import (
    UpdateProductRestrictionsRequest,
    ProductRestrictionsResponse
)
from src.services.restrictions_service import RestrictionsService
from src.dependencies import get_restrictions_service
from src.dependencies.auth import CurrentUser, get_current_user, require_admin
from src.utils.correlation_id import get_correlation_id


router = APIRouter(prefix="/restrictions", tags=["restrictions"])


@router.put(
    "/{product_id}",
    response_model=ProductRestrictionsResponse,
    summary="Update product restrictions",
    description="Update restrictions and compliance metadata for a product (admin only)"
)
async def update_product_restrictions(
    product_id: str,
    request: UpdateProductRestrictionsRequest,
    current_user: CurrentUser = Depends(require_admin),
    service: RestrictionsService = Depends(get_restrictions_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Update product restrictions and compliance metadata.
    
    **Admin only**
    
    Restrictions include:
    - Age restrictions (none, 18+, 21+, custom)
    - Shipping restrictions (hazmat, oversized, perishable, etc.)
    - Regional availability (countries, states, regions)
    - Compliance metadata (certifications, warnings, ingredients, etc.)
    """
    return await service.update_restrictions(
        product_id=product_id,
        restrictions=request.restrictions,
        updated_by=current_user.user_id,
        correlation_id=correlation_id
    )


@router.get(
    "/{product_id}",
    response_model=ProductRestrictionsResponse,
    summary="Get product restrictions",
    description="Get restrictions and compliance metadata for a product"
)
async def get_product_restrictions(
    product_id: str,
    service: RestrictionsService = Depends(get_restrictions_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get product restrictions and compliance metadata.
    
    Returns all restriction information including age limits,
    shipping restrictions, regional availability, and compliance data.
    """
    return await service.get_restrictions(
        product_id=product_id,
        correlation_id=correlation_id
    )


@router.get(
    "/{product_id}/age-eligibility",
    response_model=dict,
    summary="Check age eligibility",
    description="Check if customer meets age requirements for product"
)
async def check_age_eligibility(
    product_id: str,
    customer_age: Optional[int] = Query(None, ge=0, le=150, description="Customer's age"),
    service: RestrictionsService = Depends(get_restrictions_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Check if customer meets age requirements for product.
    
    Returns eligibility status. If customer_age is not provided and product
    has age restrictions, eligibility will be False.
    """
    eligible = await service.check_age_eligibility(
        product_id=product_id,
        customer_age=customer_age,
        correlation_id=correlation_id
    )
    
    return {
        "product_id": product_id,
        "eligible": eligible,
        "customer_age": customer_age
    }


@router.get(
    "/{product_id}/regional-availability",
    response_model=dict,
    summary="Check regional availability",
    description="Check if product is available in specified region"
)
async def check_regional_availability(
    product_id: str,
    country_code: str = Query(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"),
    state_code: Optional[str] = Query(None, max_length=10, description="State/province code"),
    service: RestrictionsService = Depends(get_restrictions_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Check if product is available in specified region.
    
    Checks country-level and state-level restrictions.
    Returns True if product is available, False otherwise.
    """
    available = await service.check_regional_availability(
        product_id=product_id,
        country_code=country_code.upper(),
        state_code=state_code.upper() if state_code else None,
        correlation_id=correlation_id
    )
    
    return {
        "product_id": product_id,
        "available": available,
        "country_code": country_code.upper(),
        "state_code": state_code.upper() if state_code else None
    }


@router.get(
    "/{product_id}/shipping-restrictions",
    response_model=dict,
    summary="Get shipping restrictions",
    description="Get list of shipping restrictions for a product"
)
async def get_shipping_restrictions(
    product_id: str,
    service: RestrictionsService = Depends(get_restrictions_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get list of shipping restrictions for a product.
    
    Returns all applicable shipping restrictions such as hazmat,
    oversized, perishable, temperature-controlled, etc.
    """
    restrictions = await service.get_applicable_shipping_restrictions(
        product_id=product_id,
        correlation_id=correlation_id
    )
    
    return {
        "product_id": product_id,
        "shipping_restrictions": restrictions,
        "has_restrictions": len(restrictions) > 0
    }
