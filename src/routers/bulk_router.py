from typing import List
from fastapi import APIRouter, status, Depends, Body
from src.models.product import ProductCreate, ProductDB
from src.db.mongodb import get_product_collection
from src.core.auth import get_current_user
from src.core.errors import ErrorResponseModel
import src.controllers.bulk_product_controller as bulk_product_controller

router = APIRouter()

@router.post("/bulk", response_model=List[ProductDB], status_code=status.HTTP_201_CREATED, responses={400: {"model": ErrorResponseModel}})
async def bulk_create_products(
    products: List[ProductCreate],
    collection=Depends(get_product_collection),
    user=Depends(get_current_user)
):
    """
    Bulk create products. Prevents duplicate SKUs and negative values.
    """
    for p in products:
        p.created_by = user["user_id"]
    return await bulk_product_controller.bulk_create_products(products, collection)

@router.patch("/bulk", response_model=List[ProductDB], responses={400: {"model": ErrorResponseModel}})
async def bulk_update_products(
    updates: List[dict] = Body(...),
    collection=Depends(get_product_collection),
    user=Depends(get_current_user)
):
    """
    Bulk update products. Only the creator or admin can update.
    """
    return await bulk_product_controller.bulk_update_products(updates, collection, user)

@router.delete("/bulk", response_model=dict, responses={400: {"model": ErrorResponseModel}})
async def bulk_delete_products(
    ids: List[str] = Body(...),
    collection=Depends(get_product_collection),
    user=Depends(get_current_user)
):
    """
    Bulk soft delete products. Only the creator or admin can delete.
    """
    return await bulk_product_controller.bulk_delete_products(ids, collection, user)
