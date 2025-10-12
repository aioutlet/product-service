import io
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse

import src.controllers.import_export_controller as import_export_controller
from src.shared.core.auth import get_current_user
from src.shared.core.errors import ErrorResponseModel
from src.shared.core.logger import logger
from src.shared.db.mongodb import get_product_collection
from src.shared.models.product import ProductDB

router = APIRouter()


@router.post(
    "/import",
    response_model=List[ProductDB],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponseModel}},
)
async def import_products(
    file: UploadFile = File(...),
    collection=Depends(get_product_collection),
    user=Depends(get_current_user),
):
    """
    Import products from a CSV or JSON file.
    """
    content = await file.read()
    filetype = file.filename.split(".")[-1].lower()
    products = await import_export_controller.import_products(
        content, filetype, collection, user
    )
    return products


@router.get(
    "/export",
    responses={
        200: {
            "content": {"application/json": {}},
            "description": "Export products as JSON or CSV.",
        }
    },
)
async def export_products(
    filetype: str = Query("json", enum=["json", "csv"], description="Export format"),
    collection=Depends(get_product_collection),
    user=Depends(get_current_user),
):
    """
    Export products as JSON or CSV file.
    """
    try:
        logger.info(
            f"Starting export with filetype: {filetype}",
            extra={
                "event": "export_start",
                "filetype": filetype,
                "user": user.get("user_id") if user else "unknown",
            },
        )
        data = await import_export_controller.export_products(collection, filetype)
        logger.info(
            "Export completed successfully",
            extra={"event": "export_success", "filetype": filetype},
        )

        if filetype == "csv":
            # Generate filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"products_export_{timestamp}.csv"
            return StreamingResponse(
                io.StringIO(data),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            # For JSON, create downloadable file
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"products_export_{timestamp}.json"
            return StreamingResponse(
                io.StringIO(data),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
    except Exception as e:
        logger.error(
            f"Export router error: {e}",
            extra={"event": "export_router_error", "error_type": type(e).__name__},
        )
        raise
