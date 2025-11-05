"""
Bulk Import API Endpoints

Handles Excel template download, file upload, and import job management.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse

from src.models.bulk_import import (
    DownloadTemplateRequest,
    ImportJobStatusResponse,
    ImportJobHistory,
    ImportJobSummary,
    ImportMode,
    ImportStatus
)
from src.services.template_generation_service import TemplateGenerationService
from src.services.import_processing_service import ImportProcessingService
from src.dependencies import get_product_repository
from src.dependencies.auth import require_admin, CurrentUser, get_current_user
from src.utils.correlation_id import get_correlation_id
from src.core.logger import logger


router = APIRouter(prefix="/bulk-import", tags=["Bulk Import"])


# In-memory job storage (in production, use Redis or database)
_import_jobs = {}


@router.post("/template/download")
async def download_template(
    category: str = Query(..., description="Product category for template"),
    include_examples: bool = Query(True, description="Include example rows"),
    current_user: CurrentUser = Depends(require_admin),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Download Excel template for bulk product import.
    
    Generates a category-specific Excel template with:
    - Column headers and descriptions
    - Data validation rules
    - Example rows (optional)
    - Instructions sheet
    
    **Requires**: Admin role
    """
    logger.info(
        f"Template download requested for category: {category}",
        metadata={"category": category, "user": current_user.user_id},
        correlation_id=correlation_id
    )
    
    try:
        service = TemplateGenerationService()
        template = service.generate_template(
            category=category,
            include_examples=include_examples,
            correlation_id=correlation_id
        )
        
        filename = f"product_import_template_{category.lower().replace(' ', '_')}.xlsx"
        
        return StreamingResponse(
            template,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(
            f"Failed to generate template: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")


@router.post("/import")
async def upload_import_file(
    file: UploadFile = File(..., description="Excel file with product data"),
    mode: ImportMode = Query(ImportMode.PARTIAL, description="Import mode"),
    category: Optional[str] = Query(None, description="Product category"),
    validate_only: bool = Query(False, description="Only validate, don't import"),
    current_user: CurrentUser = Depends(require_admin),
    repository = Depends(get_product_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Upload Excel file for bulk product import.
    
    **Process:**
    1. Validates file format and size
    2. Parses Excel and validates data
    3. Returns validation errors (if any)
    4. Imports products (unless validate_only=true)
    5. Returns job ID for tracking
    
    **Supported formats**: .xlsx, .xls  
    **Max file size**: 50MB  
    **Max products**: 10,000 per file
    
    **Import modes:**
    - `partial`: Import valid rows, skip invalid ones
    - `all_or_nothing`: Only import if ALL rows are valid
    
    **Requires**: Admin role
    """
    logger.info(
        f"Import file uploaded: {file.filename}",
        metadata={
            "filename": file.filename,
            "mode": mode,
            "validate_only": validate_only,
            "user": current_user.user_id
        },
        correlation_id=correlation_id
    )
    
    try:
        # Read file content
        content = await file.read()
        
        # Create import processing service
        service = ImportProcessingService(repository=repository)
        
        # Create import job
        job = await service.create_import_job(
            file_content=content,
            filename=file.filename,
            mode=mode,
            created_by=current_user.user_id,
            category=category,
            correlation_id=correlation_id
        )
        
        # Store job (in production, save to database)
        _import_jobs[job.job_id] = {
            "job": job,
            "file_content": content
        }
        
        # Validate file
        products, errors, warnings = await service.validate_import(
            job=job,
            file_content=content,
            correlation_id=correlation_id
        )
        
        job.validation_errors = errors
        job.validation_warnings = warnings
        
        # Check for validation errors
        if errors:
            if mode == ImportMode.ALL_OR_NOTHING:
                job.status = ImportStatus.FAILED
                job.summary_message = f"Validation failed with {len(errors)} errors. Fix errors and retry."
                logger.warning(
                    f"Import validation failed for job {job.job_id}",
                    metadata={"error_count": len(errors)},
                    correlation_id=correlation_id
                )
                return ImportJobStatusResponse(
                    job=job,
                    can_retry=True,
                    error_report_url=None
                )
            else:
                # Partial mode - filter out invalid products
                logger.warning(
                    f"Import has {len(errors)} validation errors in partial mode",
                    metadata={"error_count": len(errors), "valid_products": len(products)},
                    correlation_id=correlation_id
                )
        
        # If validate_only, stop here
        if validate_only:
            job.status = ImportStatus.COMPLETED
            job.summary_message = f"Validation complete: {len(products)} valid products, {len(errors)} errors"
            return ImportJobStatusResponse(
                job=job,
                can_retry=False,
                error_report_url=None
            )
        
        # Process import asynchronously (in production, use background task/worker)
        # For now, process synchronously
        job = await service.process_import(
            job=job,
            products=products,
            created_by=current_user.user_id,
            correlation_id=correlation_id
        )
        
        _import_jobs[job.job_id]["job"] = job
        
        logger.info(
            f"Import completed for job {job.job_id}",
            metadata={
                "status": job.status,
                "successful": job.progress.successful_rows,
                "failed": job.progress.failed_rows
            },
            correlation_id=correlation_id
        )
        
        return ImportJobStatusResponse(
            job=job,
            can_retry=job.status == ImportStatus.FAILED,
            error_report_url=None
        )
    
    except Exception as e:
        logger.error(
            f"Import failed: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/import/status/{job_id}")
async def get_import_status(
    job_id: str,
    current_user: CurrentUser = Depends(require_admin),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get status of an import job.
    
    Returns:
    - Job details and progress
    - Validation errors
    - Import results
    - Whether job can be retried
    
    **Requires**: Admin role
    """
    if job_id not in _import_jobs:
        raise HTTPException(status_code=404, detail=f"Import job {job_id} not found")
    
    job = _import_jobs[job_id]["job"]
    
    return ImportJobStatusResponse(
        job=job,
        can_retry=job.status in [ImportStatus.FAILED, ImportStatus.PARTIAL],
        error_report_url=job.error_report_path
    )


@router.get("/import/history", response_model=ImportJobHistory)
async def get_import_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ImportStatus] = Query(None, description="Filter by status"),
    current_user: CurrentUser = Depends(require_admin),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get import job history.
    
    Returns paginated list of import jobs with summary information.
    
    **Query parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `status`: Filter by job status (optional)
    
    **Requires**: Admin role
    """
    # Get all jobs (in production, query from database)
    all_jobs = [data["job"] for data in _import_jobs.values()]
    
    # Filter by status
    if status:
        all_jobs = [job for job in all_jobs if job.status == status]
    
    # Sort by created_at descending
    all_jobs.sort(key=lambda j: j.created_at, reverse=True)
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_jobs = all_jobs[start:end]
    
    # Convert to summaries
    summaries = [
        ImportJobSummary(
            job_id=job.job_id,
            filename=job.filename,
            status=job.status,
            mode=job.mode,
            created_by=job.created_by,
            created_at=job.created_at,
            completed_at=job.completed_at,
            total_rows=job.progress.total_rows,
            successful_rows=job.progress.successful_rows,
            failed_rows=job.progress.failed_rows,
            summary_message=job.summary_message
        )
        for job in page_jobs
    ]
    
    return ImportJobHistory(
        jobs=summaries,
        total=len(all_jobs),
        page=page,
        page_size=page_size,
        has_more=end < len(all_jobs)
    )


@router.post("/import/{job_id}/retry")
async def retry_import(
    job_id: str,
    current_user: CurrentUser = Depends(require_admin),
    repository = Depends(get_product_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Retry a failed import job.
    
    Re-runs the import using the original file.
    Useful after fixing data issues externally.
    
    **Requires**: Admin role
    """
    if job_id not in _import_jobs:
        raise HTTPException(status_code=404, detail=f"Import job {job_id} not found")
    
    job_data = _import_jobs[job_id]
    old_job = job_data["job"]
    
    if old_job.status not in [ImportStatus.FAILED, ImportStatus.PARTIAL]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry job with status {old_job.status}"
        )
    
    logger.info(
        f"Retrying import job {job_id}",
        metadata={"original_status": old_job.status},
        correlation_id=correlation_id
    )
    
    try:
        service = ImportProcessingService(repository=repository)
        
        # Create new job
        new_job = await service.create_import_job(
            file_content=job_data["file_content"],
            filename=old_job.filename,
            mode=old_job.mode,
            created_by=current_user.user_id,
            category=old_job.category,
            correlation_id=correlation_id
        )
        
        # Validate and process
        products, errors, warnings = await service.validate_import(
            job=new_job,
            file_content=job_data["file_content"],
            correlation_id=correlation_id
        )
        
        new_job.validation_errors = errors
        new_job.validation_warnings = warnings
        
        if not errors or new_job.mode == ImportMode.PARTIAL:
            new_job = await service.process_import(
                job=new_job,
                products=products,
                created_by=current_user.user_id,
                correlation_id=correlation_id
            )
        else:
            new_job.status = ImportStatus.FAILED
            new_job.summary_message = f"Validation failed with {len(errors)} errors"
        
        # Store new job
        _import_jobs[new_job.job_id] = {
            "job": new_job,
            "file_content": job_data["file_content"]
        }
        
        return ImportJobStatusResponse(
            job=new_job,
            can_retry=new_job.status == ImportStatus.FAILED,
            error_report_url=None
        )
    
    except Exception as e:
        logger.error(
            f"Retry failed: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")


@router.delete("/import/{job_id}")
async def delete_import_job(
    job_id: str,
    current_user: CurrentUser = Depends(require_admin),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Delete an import job and its associated files.
    
    **Requires**: Admin role
    """
    if job_id not in _import_jobs:
        raise HTTPException(status_code=404, detail=f"Import job {job_id} not found")
    
    logger.info(
        f"Deleting import job {job_id}",
        metadata={"user": current_user.user_id},
        correlation_id=correlation_id
    )
    
    del _import_jobs[job_id]
    
    return {"message": f"Import job {job_id} deleted successfully"}
