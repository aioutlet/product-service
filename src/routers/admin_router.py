"""
Admin Router
Handles admin-specific operations for product management.
Implements PRD REQ-5.x: Admin features
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Body, Query, status, UploadFile, File
from fastapi.responses import Response

from src.security import User, require_admin
from src.core.errors import ErrorResponse
from src.db.mongodb import get_product_collection
from src.controllers.product_controller import get_admin_stats
from src.services.dapr_publisher import get_dapr_publisher
from src.services.bulk_import_service import get_bulk_import_service
from src.observability.logging import logger
from src.utils.validators import validate_object_id
from src.models.admin_models import SizeChart, ProductRestrictions

router = APIRouter()


# ============================================================================
# REQ-5.1: Product Statistics & Reporting
# ============================================================================

@router.get(
    "/stats",
    response_model=dict,
    summary="Get product statistics",
    description="Returns product statistics for admin dashboard (REQ-5.1)"
)
async def get_product_stats(
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Get product statistics including total, active, and inactive counts."""
    return await get_admin_stats(collection)


# ============================================================================
# REQ-5.3: Badge Management (Manual Control)
# ============================================================================

@router.post(
    "/products/{product_id}/badges",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Manually assign badge to product",
    description="Admin can manually assign badges with expiration dates (REQ-5.3.1)"
)
async def assign_badge_to_product(
    product_id: str,
    badge_type: str = Body(..., embed=True),
    expires_at: Optional[datetime] = Body(None, embed=True),
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """
    Manually assign a badge to a product.
    Supports manual badge types: limited-time-deal, featured, exclusive,
    pre-order, clearance, eco-friendly, custom.
    """
    try:
        # Validate product ID
        obj_id = validate_object_id(product_id)
        
        # Find product
        product = await collection.find_one({"_id": obj_id})
        if not product:
            raise ErrorResponse("Product not found", status_code=404)
        
        # Get current badges
        badges = product.get('badges', [])
        
        # Check if badge already exists
        existing_badge = next(
            (b for b in badges if b.get('badge_type') == badge_type),
            None
        )
        if existing_badge:
            raise ErrorResponse(
                f"Badge '{badge_type}' already assigned to this product",
                status_code=400
            )
        
        # Create new badge
        new_badge = {
            'badge_type': badge_type,
            'assigned_at': datetime.now(timezone.utc),
            'expires_at': expires_at,
            'auto_assigned': False,  # Manually assigned
            'assigned_by': user.user_id,
            'criteria': {}
        }
        
        badges.append(new_badge)
        
        # Update product
        await collection.update_one(
            {"_id": obj_id},
            {"$set": {"badges": badges}}
        )
        
        # Publish badge.assigned event (NOT product.updated)
        publisher = get_dapr_publisher()
        await publisher.publish(
            'product.badge.manually.assigned',
            {
                'productId': product_id,
                'badgeType': badge_type,
                'assignedBy': user.user_id,
                'assignedAt': new_badge['assigned_at'].isoformat(),
                'expiresAt': expires_at.isoformat() if expires_at else None
            },
            None
        )
        
        logger.info(
            f"Manually assigned badge {badge_type} to product {product_id}",
            metadata={
                'event': 'badge_manually_assigned',
                'productId': product_id,
                'badgeType': badge_type,
                'assignedBy': user.user_id
            }
        )
        
        return {
            "message": "Badge assigned successfully",
            "badge": new_badge
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to assign badge: {str(e)}",
            metadata={'error': str(e), 'productId': product_id}
        )
        raise ErrorResponse(
            f"Failed to assign badge: {str(e)}",
            status_code=500
        )


@router.delete(
    "/products/{product_id}/badges/{badge_type}",
    response_model=dict,
    summary="Remove badge from product",
    description="Admin can manually remove badges (REQ-5.3.1)"
)
async def remove_badge_from_product(
    product_id: str,
    badge_type: str,
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Remove a badge from a product."""
    try:
        # Validate product ID
        obj_id = validate_object_id(product_id)
        
        # Find product
        product = await collection.find_one({"_id": obj_id})
        if not product:
            raise ErrorResponse("Product not found", status_code=404)
        
        # Get current badges
        badges = product.get('badges', [])
        
        # Find and remove badge
        badge_found = False
        new_badges = []
        for badge in badges:
            if badge.get('badge_type') == badge_type:
                badge_found = True
            else:
                new_badges.append(badge)
        
        if not badge_found:
            raise ErrorResponse(
                f"Badge '{badge_type}' not found on this product",
                status_code=404
            )
        
        # Update product
        await collection.update_one(
            {"_id": obj_id},
            {"$set": {"badges": new_badges}}
        )
        
        # Publish badge.removed event
        publisher = get_dapr_publisher()
        await publisher.publish(
            'product.badge.manually.removed',
            {
                'productId': product_id,
                'badgeType': badge_type,
                'removedBy': user.user_id,
                'removedAt': datetime.now(timezone.utc).isoformat()
            },
            None
        )
        
        logger.info(
            f"Removed badge {badge_type} from product {product_id}",
            metadata={
                'event': 'badge_manually_removed',
                'productId': product_id,
                'badgeType': badge_type,
                'removedBy': user.user_id
            }
        )
        
        return {
            "message": "Badge removed successfully",
            "badgeType": badge_type
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to remove badge: {str(e)}",
            metadata={'error': str(e), 'productId': product_id}
        )
        raise ErrorResponse(
            f"Failed to remove badge: {str(e)}",
            status_code=500
        )


@router.get(
    "/badges",
    response_model=dict,
    summary="Get all products with specific badge",
    description="Admin can view all products with a specific badge (REQ-5.3.3)"
)
async def get_products_by_badge(
    badge_type: str = Query(..., description="Badge type to filter by"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Get all products with a specific badge type."""
    try:
        # Query products with this badge
        cursor = collection.find(
            {"badges.badge_type": badge_type},
            {
                "_id": 1,
                "name": 1,
                "sku": 1,
                "badges": 1,
                "price": 1
            }
        ).skip(skip).limit(limit)
        
        products = await cursor.to_list(length=limit)
        
        # Get total count
        total = await collection.count_documents(
            {"badges.badge_type": badge_type}
        )
        
        # Format response
        result_products = []
        for product in products:
            # Find the specific badge
            badge = next(
                (b for b in product.get('badges', [])
                 if b.get('badge_type') == badge_type),
                None
            )
            
            result_products.append({
                "productId": str(product['_id']),
                "name": product.get('name'),
                "sku": product.get('sku'),
                "price": product.get('price'),
                "badge": badge
            })
        
        return {
            "badgeType": badge_type,
            "products": result_products,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(
            f"Failed to get products by badge: {str(e)}",
            metadata={'error': str(e), 'badgeType': badge_type}
        )
        raise ErrorResponse(
            f"Failed to get products by badge: {str(e)}",
            status_code=500
        )


@router.post(
    "/badges/bulk-assign",
    response_model=dict,
    summary="Bulk assign badges to multiple products",
    description="Admin can bulk assign badges (REQ-5.3.1)"
)
async def bulk_assign_badges(
    product_ids: List[str] = Body(...),
    badge_type: str = Body(...),
    expires_at: Optional[datetime] = Body(None),
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Bulk assign a badge to multiple products."""
    try:
        success_count = 0
        failed_products = []
        
        for product_id in product_ids:
            try:
                # Validate and convert product ID
                obj_id = validate_object_id(product_id)
                
                # Find product
                product = await collection.find_one({"_id": obj_id})
                if not product:
                    failed_products.append({
                        "productId": product_id,
                        "reason": "Product not found"
                    })
                    continue
                
                # Get current badges
                badges = product.get('badges', [])
                
                # Check if badge already exists
                if any(b.get('badge_type') == badge_type for b in badges):
                    failed_products.append({
                        "productId": product_id,
                        "reason": "Badge already exists"
                    })
                    continue
                
                # Create new badge
                new_badge = {
                    'badge_type': badge_type,
                    'assigned_at': datetime.now(timezone.utc),
                    'expires_at': expires_at,
                    'auto_assigned': False,
                    'assigned_by': user.user_id,
                    'criteria': {}
                }
                
                badges.append(new_badge)
                
                # Update product
                await collection.update_one(
                    {"_id": obj_id},
                    {"$set": {"badges": badges}}
                )
                
                success_count += 1
                
            except Exception as e:
                failed_products.append({
                    "productId": product_id,
                    "reason": str(e)
                })
        
        logger.info(
            f"Bulk assigned badge {badge_type} to {success_count} products",
            metadata={
                'event': 'badge_bulk_assigned',
                'badgeType': badge_type,
                'successCount': success_count,
                'failedCount': len(failed_products),
                'assignedBy': user.user_id
            }
        )
        
        return {
            "message": "Bulk badge assignment completed",
            "successCount": success_count,
            "failedCount": len(failed_products),
            "failedProducts": failed_products
        }
        
    except Exception as e:
        logger.error(
            f"Failed to bulk assign badges: {str(e)}",
            metadata={'error': str(e), 'badgeType': badge_type}
        )
        raise ErrorResponse(
            f"Failed to bulk assign badges: {str(e)}",
            status_code=500
        )


# ============================================================================
# REQ-5.4: Size Chart Management
# ============================================================================

@router.post(
    "/size-charts",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create size chart",
    description="Admin can create size charts for categories (REQ-5.4.1)"
)
async def create_size_chart(
    size_chart: SizeChart,
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Create a new size chart for a product category."""
    try:
        # Get database
        db = collection.database
        size_charts_collection = db.get_collection("size_charts")
        
        # Prepare document
        size_chart.created_by = user.user_id
        size_chart.created_at = datetime.now(timezone.utc)
        size_chart.updated_at = datetime.now(timezone.utc)
        
        size_chart_dict = size_chart.dict(exclude={'id'})
        
        # Insert into database
        result = await size_charts_collection.insert_one(size_chart_dict)
        
        logger.info(
            f"Created size chart: {size_chart.name}",
            metadata={
                'event': 'size_chart_created',
                'sizeChartId': str(result.inserted_id),
                'category': size_chart.category,
                'createdBy': user.user_id
            }
        )
        
        return {
            "message": "Size chart created successfully",
            "sizeChartId": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(
            f"Failed to create size chart: {str(e)}",
            metadata={'error': str(e)}
        )
        raise ErrorResponse(
            f"Failed to create size chart: {str(e)}",
            status_code=500
        )


@router.get(
    "/size-charts",
    response_model=dict,
    summary="List size charts",
    description="Get all size charts, optionally filtered by category (REQ-5.4.1)"
)
async def list_size_charts(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """List all size charts with optional category filter."""
    try:
        # Get database
        db = collection.database
        size_charts_collection = db.get_collection("size_charts")
        
        # Build query
        query = {}
        if category:
            query['category'] = category
        
        # Get size charts
        cursor = size_charts_collection.find(query).skip(skip).limit(limit)
        size_charts = await cursor.to_list(length=limit)
        
        # Get total count
        total = await size_charts_collection.count_documents(query)
        
        # Convert ObjectId to string
        for chart in size_charts:
            chart['id'] = str(chart.pop('_id'))
        
        return {
            "sizeCharts": size_charts,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(
            f"Failed to list size charts: {str(e)}",
            metadata={'error': str(e)}
        )
        raise ErrorResponse(
            f"Failed to list size charts: {str(e)}",
            status_code=500
        )


@router.put(
    "/products/{product_id}/size-chart",
    response_model=dict,
    summary="Assign size chart to product",
    description="Admin can assign size chart to product (REQ-5.4.1)"
)
async def assign_size_chart_to_product(
    product_id: str,
    size_chart_id: str = Body(..., embed=True),
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Assign a size chart to a product."""
    try:
        # Validate product ID
        obj_id = validate_object_id(product_id)
        
        # Validate size chart exists
        db = collection.database
        size_charts_collection = db.get_collection("size_charts")
        
        size_chart_obj_id = validate_object_id(size_chart_id)
        size_chart = await size_charts_collection.find_one(
            {"_id": size_chart_obj_id}
        )
        if not size_chart:
            raise ErrorResponse("Size chart not found", status_code=404)
        
        # Update product
        result = await collection.update_one(
            {"_id": obj_id},
            {"$set": {"size_chart_id": size_chart_id}}
        )
        
        if result.matched_count == 0:
            raise ErrorResponse("Product not found", status_code=404)
        
        logger.info(
            f"Assigned size chart {size_chart_id} to product {product_id}",
            metadata={
                'event': 'size_chart_assigned',
                'productId': product_id,
                'sizeChartId': size_chart_id,
                'assignedBy': user.user_id
            }
        )
        
        return {
            "message": "Size chart assigned successfully",
            "sizeChartId": size_chart_id
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to assign size chart: {str(e)}",
            metadata={'error': str(e), 'productId': product_id}
        )
        raise ErrorResponse(
            f"Failed to assign size chart: {str(e)}",
            status_code=500
        )


# ============================================================================
# REQ-5.5: Product Restrictions & Compliance
# ============================================================================

@router.put(
    "/products/{product_id}/restrictions",
    response_model=dict,
    summary="Update product restrictions",
    description="Admin can configure product restrictions and compliance (REQ-5.5)"
)
async def update_product_restrictions(
    product_id: str,
    restrictions: ProductRestrictions,
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Update product restrictions and compliance metadata."""
    try:
        # Validate product ID
        obj_id = validate_object_id(product_id)
        
        # Update product
        result = await collection.update_one(
            {"_id": obj_id},
            {"$set": {"restrictions": restrictions.dict()}}
        )
        
        if result.matched_count == 0:
            raise ErrorResponse("Product not found", status_code=404)
        
        logger.info(
            f"Updated restrictions for product {product_id}",
            metadata={
                'event': 'restrictions_updated',
                'productId': product_id,
                'updatedBy': user.user_id
            }
        )
        
        return {
            "message": "Product restrictions updated successfully",
            "productId": product_id
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to update restrictions: {str(e)}",
            metadata={'error': str(e), 'productId': product_id}
        )
        raise ErrorResponse(
            f"Failed to update restrictions: {str(e)}",
            status_code=500
        )


@router.get(
    "/products/{product_id}/restrictions",
    response_model=dict,
    summary="Get product restrictions",
    description="Get product restrictions and compliance metadata (REQ-5.5)"
)
async def get_product_restrictions(
    product_id: str,
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """Get product restrictions and compliance metadata."""
    try:
        # Validate product ID
        obj_id = validate_object_id(product_id)
        
        # Find product
        product = await collection.find_one(
            {"_id": obj_id},
            {"restrictions": 1, "name": 1, "sku": 1}
        )
        
        if not product:
            raise ErrorResponse("Product not found", status_code=404)
        
        return {
            "productId": product_id,
            "name": product.get('name'),
            "sku": product.get('sku'),
            "restrictions": product.get('restrictions', {})
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get restrictions: {str(e)}",
            metadata={'error': str(e), 'productId': product_id}
        )
        raise ErrorResponse(
            f"Failed to get restrictions: {str(e)}",
            status_code=500
        )


# ============================================================================
# REQ-5.2: Bulk Product Operations
# ============================================================================

@router.get(
    "/bulk-import/template",
    summary="Download Excel import template",
    description="Download category-specific Excel template for bulk import (REQ-5.2.1)"
)
async def download_import_template(
    category: Optional[str] = Query(None, description="Category for template"),
    user: User = Depends(require_admin)
):
    """
    Download Excel template for bulk product import.
    Template includes field descriptions, validation rules, and examples.
    """
    try:
        bulk_service = get_bulk_import_service()
        template_content = bulk_service.generate_excel_template(category)
        
        filename = f"product_import_template_{category or 'general'}.xlsx"
        
        logger.info(
            f"Generated import template for category: {category}",
            metadata={
                'event': 'template_downloaded',
                'category': category,
                'downloadedBy': user.user_id
            }
        )
        
        return Response(
            content=template_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(
            f"Failed to generate template: {str(e)}",
            metadata={'error': str(e)}
        )
        raise ErrorResponse(
            f"Failed to generate template: {str(e)}",
            status_code=500
        )


@router.post(
    "/bulk-import/validate",
    response_model=dict,
    summary="Validate bulk import file",
    description="Validate Excel file and return validation errors (REQ-5.2.2)"
)
async def validate_import_file(
    file: UploadFile = File(..., description="Excel file to validate"),
    user: User = Depends(require_admin)
):
    """
    Validate bulk import file without importing.
    Returns validation errors and valid product count.
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise ErrorResponse(
                "Only Excel files (.xlsx, .xls) are supported",
                status_code=400
            )
        
        # Read file content
        content = await file.read()
        
        # Validate
        bulk_service = get_bulk_import_service()
        valid_products, errors = bulk_service.validate_import_data(
            content,
            file.filename
        )
        
        logger.info(
            f"Validated import file: {file.filename}",
            metadata={
                'event': 'import_file_validated',
                'filename': file.filename,
                'validCount': len(valid_products),
                'errorCount': len(errors),
                'validatedBy': user.user_id
            }
        )
        
        return {
            "filename": file.filename,
            "validProductCount": len(valid_products),
            "errorCount": len(errors),
            "errors": [e.dict() for e in errors]
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to validate file: {str(e)}",
            metadata={'error': str(e), 'filename': file.filename}
        )
        raise ErrorResponse(
            f"Failed to validate file: {str(e)}",
            status_code=500
        )


@router.post(
    "/bulk-import",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start bulk product import",
    description="Start async bulk import job (REQ-5.2.2)"
)
async def start_bulk_import(
    file: UploadFile = File(..., description="Excel file to import"),
    import_mode: str = Query("partial", enum=["partial", "all-or-nothing"]),
    collection=Depends(get_product_collection),
    user: User = Depends(require_admin)
):
    """
    Start asynchronous bulk product import.
    
    Modes:
    - partial: Skip invalid rows, import valid ones
    - all-or-nothing: Rollback if any row fails
    
    Returns job ID for tracking progress.
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise ErrorResponse(
                "Only Excel files (.xlsx, .xls) are supported",
                status_code=400
            )
        
        # Read and validate file
        content = await file.read()
        bulk_service = get_bulk_import_service()
        valid_products, errors = bulk_service.validate_import_data(
            content,
            file.filename
        )
        
        if not valid_products:
            raise ErrorResponse(
                "No valid products found in file",
                status_code=400,
                details={"errors": [e.dict() for e in errors]}
            )
        
        # Create import job
        job = await bulk_service.create_import_job(
            filename=file.filename,
            total_rows=len(valid_products),
            created_by=user.user_id,
            import_mode=import_mode
        )
        
        # Publish job created event (background worker will process)
        await bulk_service.publish_import_job_event(
            job.job_id,
            "product.bulk.import.job.created",
            {
                "filename": file.filename,
                "totalRows": len(valid_products),
                "importMode": import_mode,
                "createdBy": user.user_id,
                "products": valid_products  # Pass products to worker
            }
        )
        
        logger.info(
            f"Started bulk import job: {job.job_id}",
            metadata={
                'event': 'bulk_import_started',
                'jobId': job.job_id,
                'filename': file.filename,
                'totalRows': len(valid_products),
                'mode': import_mode,
                'startedBy': user.user_id
            }
        )
        
        return {
            "message": "Import job started",
            "jobId": job.job_id,
            "totalRows": len(valid_products),
            "errorCount": len(errors),
            "status": "pending"
        }
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to start import: {str(e)}",
            metadata={'error': str(e), 'filename': file.filename}
        )
        raise ErrorResponse(
            f"Failed to start import: {str(e)}",
            status_code=500
        )


@router.get(
    "/bulk-import/jobs/{job_id}",
    response_model=dict,
    summary="Get import job status",
    description="Get status and progress of import job (REQ-5.2.4)"
)
async def get_import_job_status(
    job_id: str,
    user: User = Depends(require_admin)
):
    """Get import job status and progress."""
    try:
        bulk_service = get_bulk_import_service()
        job = await bulk_service.get_import_job(job_id)
        
        if not job:
            raise ErrorResponse("Import job not found", status_code=404)
        
        # Remove _id field
        job.pop('_id', None)
        
        return job
        
    except ErrorResponse:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get job status: {str(e)}",
            metadata={'error': str(e), 'jobId': job_id}
        )
        raise ErrorResponse(
            f"Failed to get job status: {str(e)}",
            status_code=500
        )


@router.get(
    "/bulk-import/jobs",
    response_model=dict,
    summary="List import jobs",
    description="List import job history with pagination (REQ-5.2.4)"
)
async def list_import_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, enum=["pending", "processing", "completed", "failed", "cancelled"]),
    user: User = Depends(require_admin)
):
    """List import jobs with optional status filter."""
    try:
        bulk_service = get_bulk_import_service()
        jobs, total = await bulk_service.list_import_jobs(skip, limit, status)
        
        # Remove _id fields
        for job in jobs:
            job.pop('_id', None)
        
        return {
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(
            f"Failed to list jobs: {str(e)}",
            metadata={'error': str(e)}
        )
        raise ErrorResponse(
            f"Failed to list jobs: {str(e)}",
            status_code=500
        )
