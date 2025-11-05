"""
Admin-only API endpoints.

Administrative operations for product management, statistics, and bulk operations.
"""

from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timedelta
import io

from src.dependencies.auth import require_admin, CurrentUser
from src.dependencies import get_products_collection, get_correlation_id
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
    Get basic product statistics for admin dashboard.
    
    Returns total products, active products, and category breakdowns.
    """
    from src.services.product_service import ProductService
    from src.repositories.product_repository import ProductRepository
    
    repo = ProductRepository(collection)
    service = ProductService(repo)
    return await service.get_admin_stats(collection)


@router.get("/dashboard/stats", response_model=dict)
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for trend analysis"),
    collection: AsyncIOMotorCollection = Depends(get_products_collection),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get comprehensive dashboard statistics for admin.
    
    Returns detailed metrics including:
    - Product counts by status
    - Category distribution
    - Recent activity (products added/updated)
    - Variations statistics
    - Badge statistics
    - Size chart statistics
    - Product trends
    - Price statistics
    
    Args:
        days: Number of days for trend analysis (default: 30)
        
    Returns:
        Comprehensive admin dashboard statistics
    """
    from datetime import timezone
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Product counts by status
    total_products = await collection.count_documents({})
    active_products = await collection.count_documents({"is_active": True})
    inactive_products = await collection.count_documents({"is_active": False})
    draft_products = await collection.count_documents({"status": "draft"})
    
    # Category distribution
    category_pipeline = [
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "active_count": {
                "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
            }
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    category_stats = await collection.aggregate(category_pipeline).to_list(length=10)
    
    # Recent activity
    recent_added = await collection.count_documents({
        "created_at": {"$gte": cutoff_date}
    })
    recent_updated = await collection.count_documents({
        "updated_at": {"$gte": cutoff_date},
        "created_at": {"$lt": cutoff_date}  # Exclude newly created
    })
    
    # Variations statistics
    parent_products = await collection.count_documents({"has_variations": True})
    variation_products = await collection.count_documents({"parent_product_id": {"$exists": True, "$ne": None}})
    
    # Badge statistics
    with_badges = await collection.count_documents({"badges": {"$exists": True, "$ne": []}})
    badge_distribution_pipeline = [
        {"$unwind": "$badges"},
        {"$group": {
            "_id": "$badges.type",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    badge_stats = await collection.aggregate(badge_distribution_pipeline).to_list(length=20)
    
    # Price statistics
    price_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": None,
            "avg_price": {"$avg": "$price"},
            "min_price": {"$min": "$price"},
            "max_price": {"$max": "$price"}
        }}
    ]
    price_stats_result = await collection.aggregate(price_pipeline).to_list(length=1)
    price_stats = price_stats_result[0] if price_stats_result else {
        "avg_price": 0,
        "min_price": 0,
        "max_price": 0
    }
    
    # Products with attributes
    with_structured_attrs = await collection.count_documents({
        "structured_attributes": {"$exists": True, "$ne": None}
    })
    
    # Products with restrictions
    with_restrictions = await collection.count_documents({
        "restrictions": {"$exists": True}
    })
    
    # Top brands
    brand_pipeline = [
        {"$match": {"is_active": True, "brand": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": "$brand",
            "product_count": {"$sum": 1}
        }},
        {"$sort": {"product_count": -1}},
        {"$limit": 10}
    ]
    top_brands = await collection.aggregate(brand_pipeline).to_list(length=10)
    
    # Growth trend (products added per day for last N days)
    growth_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$created_at"
                }
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    growth_trend = await collection.aggregate(growth_pipeline).to_list(length=days)
    
    return {
        "overview": {
            "total_products": total_products,
            "active_products": active_products,
            "inactive_products": inactive_products,
            "draft_products": draft_products
        },
        "recent_activity": {
            "period_days": days,
            "products_added": recent_added,
            "products_updated": recent_updated
        },
        "categories": {
            "total_categories": len(category_stats),
            "distribution": [
                {
                    "category": stat["_id"],
                    "total": stat["count"],
                    "active": stat["active_count"]
                }
                for stat in category_stats
            ]
        },
        "variations": {
            "parent_products": parent_products,
            "variation_products": variation_products,
            "avg_variations_per_parent": round(variation_products / parent_products, 2) if parent_products > 0 else 0
        },
        "badges": {
            "products_with_badges": with_badges,
            "distribution": [
                {
                    "badge_type": stat["_id"],
                    "count": stat["count"]
                }
                for stat in badge_stats
            ]
        },
        "pricing": {
            "average_price": round(price_stats.get("avg_price", 0), 2),
            "minimum_price": round(price_stats.get("min_price", 0), 2),
            "maximum_price": round(price_stats.get("max_price", 0), 2)
        },
        "features": {
            "with_structured_attributes": with_structured_attrs,
            "with_restrictions": with_restrictions
        },
        "top_brands": [
            {
                "brand": brand["_id"],
                "product_count": brand["product_count"]
            }
            for brand in top_brands
        ],
        "growth_trend": [
            {
                "date": trend["_id"],
                "products_added": trend["count"]
            }
            for trend in growth_trend
        ]
    }


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
