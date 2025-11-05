"""
Product API endpoints.

FastAPI route handlers for product CRUD operations, search, and variations.
"""

from fastapi import APIRouter, Depends, Query, Response, status, HTTPException
from typing import List, Optional

from src.dependencies.auth import CurrentUser, get_current_user, get_optional_user, require_admin
from src.dependencies import get_products_collection, get_product_service
from src.services.product_service import ProductService
from src.core.errors import ErrorResponseModel
from src.models.product import ProductDB, ProductCreate, ProductUpdate, ProductSearchResponse
from motor.motor_asyncio import AsyncIOMotorCollection

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductDB,
    dependencies=[Depends(require_admin)]
)
async def create_product(
    data: ProductCreate,
    collection=Depends(get_products_collection),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new product.
    
    Requires admin role.
    """
    from src.services.product_service import ProductService
    from src.repositories.product_repository import ProductRepository
    
    repo = ProductRepository(collection)
    service = ProductService(repo)
    product_id = await service.create_product(data.dict(), collection, current_user)
    
    # Retrieve the created product
    from src.validators.product_validators import validate_object_id
    obj_id = validate_object_id(product_id)
    doc = await collection.find_one({"_id": obj_id})
    return service._doc_to_model(doc)


@router.get(
    "/search",
    response_model=dict,
    responses={400: {"model": ErrorResponseModel}, 404: {"model": ErrorResponseModel}}
)
async def search_products(
    response: Response,
    q: str = Query(..., description="Search text", min_length=1),
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    tags: Optional[List[str]] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    collection=Depends(get_products_collection)
):
    """
    Search products by text with optional filters.
    
    Supports hierarchical filtering by department/category/subcategory.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    from src.services.product_service import ProductService
    from src.repositories.product_repository import ProductRepository
    
    repo = ProductRepository(collection)
    service = ProductService(repo)
    
    products, total = await service.search_products(
        search_text=q,
        department=department,
        category=category,
        subcategory=subcategory,
        min_price=min_price,
        max_price=max_price,
        tags=tags,
        skip=skip,
        limit=limit
    )
    
    return {
        "products": products,
        "total_count": total,
        "current_page": (skip // limit) + 1 if limit > 0 else 1,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 1
    }


@router.get(
    "/{product_id}",
    response_model=ProductDB
)
async def get_product(
    product_id: str,
    service: ProductService = Depends(get_product_service)
):
    """Get a product by ID."""
    product = await service.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.put(
    "/{product_id}",
    response_model=ProductDB,
    dependencies=[Depends(require_admin)]
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    collection=Depends(get_products_collection),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a product.
    
    Requires admin role.
    """
    from src.services.product_service import ProductService
    from src.repositories.product_repository import ProductRepository
    
    repo = ProductRepository(collection)
    service = ProductService(repo)
    product = await service.update_product(
        product_id, data.dict(exclude_unset=True), collection, current_user
    )
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)]
)
async def delete_product(
    product_id: str,
    collection=Depends(get_products_collection),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a product (soft delete).
    
    Requires admin role.
    """
    from src.services.product_service import ProductService
    from src.repositories.product_repository import ProductRepository
    
    repo = ProductRepository(collection)
    service = ProductService(repo)
    await service.delete_product(product_id, collection, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
