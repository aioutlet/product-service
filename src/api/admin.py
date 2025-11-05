"""
Admin-only API endpoints.

Administrative operations for product management, statistics, and bulk operations.
"""

from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
import io

from src.dependencies.auth import require_admin, CurrentUser
from src.dependencies import get_products_collection
from src.models.product import ProductCreate, ProductDB
from src.core.errors import ErrorResponseModel
from src.services.product_service import ProductService
from src.services.bulk_operations_service import BulkOperationsService
from src.services.import_export_service import ImportExportService
from src.repositories.product_repository import ProductRepository
from motor.motor_asyncio import AsyncIOMotorCollection

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats", response_model=dict)
async def get_admin_stats(
    collection: AsyncIOMotorCollection = Depends(get_products_collection)
):
    """
    Get product statistics for admin dashboard.
    
    Returns total products, active products, and category breakdowns.
    """
    from src.services.product_service import ProductService
    from src.repositories.product_repository import ProductRepository
    
    repo = ProductRepository(collection)
    service = ProductService(repo)
    return await service.get_admin_stats(collection)


# Bulk Operations
@router.post(
    "/bulk",
    response_model=List[ProductDB],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponseModel}}
)
async def bulk_create_products(
    products: List[ProductCreate],
    collection: AsyncIOMotorCollection = Depends(get_products_collection),
    user: CurrentUser = Depends(require_admin)
):
    """
    Create multiple products in a single request.
    
    Maximum 100 products per request.
    """
    repo = ProductRepository(collection)
    service = BulkOperationsService(repo)
    return await service.bulk_create(products, user)


@router.put(
    "/bulk",
    response_model=List[ProductDB],
    responses={400: {"model": ErrorResponseModel}}
)
async def bulk_update_products(
    updates: List[dict],
    collection: AsyncIOMotorCollection = Depends(get_products_collection),
    user: CurrentUser = Depends(require_admin)
):
    """
    Update multiple products in a single request.
    
    Each update should include 'id' and fields to update.
    """
    repo = ProductRepository(collection)
    product_service = ProductService(repo)
    bulk_service = BulkOperationsService(repo)
    return await bulk_service.bulk_update(updates, product_service, user)


@router.delete(
    "/bulk",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": ErrorResponseModel}}
)
async def bulk_delete_products(
    product_ids: List[str],
    collection: AsyncIOMotorCollection = Depends(get_products_collection),
    user: CurrentUser = Depends(require_admin)
):
    """
    Delete multiple products in a single request (soft delete).
    
    Maximum 100 products per request.
    """
    repo = ProductRepository(collection)
    service = BulkOperationsService(repo)
    await service.bulk_delete(product_ids, user)


# Import/Export Operations
@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED
)
async def import_products(
    file: UploadFile = File(...),
    collection: AsyncIOMotorCollection = Depends(get_products_collection),
    user: CurrentUser = Depends(require_admin)
):
    """
    Import products from CSV or JSON file.
    
    Validates and creates products in bulk.
    """
    # Determine file type from extension
    filename = file.filename or ""
    if filename.endswith(".csv"):
        filetype = "csv"
    elif filename.endswith(".json"):
        filetype = "json"
    else:
        from src.core.errors import ErrorResponse
        raise ErrorResponse("Unsupported file format. Use CSV or JSON.", status_code=400)
    
    # Read file content
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8")
    
    # Import using service
    repo = ProductRepository(collection)
    service = ImportExportService(repo)
    return await service.import_products(content, filetype, user)


@router.get("/export")
async def export_products(
    format: str = "csv",
    collection: AsyncIOMotorCollection = Depends(get_products_collection),
    user: CurrentUser = Depends(require_admin)
):
    """
    Export all products to CSV or JSON format.
    
    Returns a downloadable file.
    """
    repo = ProductRepository(collection)
    service = ImportExportService(repo)
    content = await service.export_products(format)
    
    # Determine content type and filename
    if format == "csv":
        media_type = "text/csv"
        filename = "products_export.csv"
    else:
        media_type = "application/json"
        filename = "products_export.json"
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
