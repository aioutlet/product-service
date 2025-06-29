from fastapi import APIRouter, status, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.models.review import Review, ReviewReport
from src.db.mongodb import get_product_collection
from src.core.auth import get_current_user
from src.core.errors import ErrorResponseModel
import src.controllers.review_controller as review_controller

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

@router.get("/{product_id}/reviews", response_model=list[Review], responses={404: {"model": ErrorResponseModel}})
async def list_reviews(product_id: str, collection=Depends(get_product_collection)):
    """
    List all reviews for a product.
    """
    return await review_controller.list_reviews(product_id, collection)

@router.post("/{product_id}/reviews", response_model=Review, status_code=status.HTTP_201_CREATED, responses={400: {"model": ErrorResponseModel}, 429: {"description": "Rate limit exceeded"}})
@limiter.limit("5/minute")
async def add_review(product_id: str, review: Review, collection=Depends(get_product_collection), user=Depends(get_current_user), request: Request = None):
    """
    Add a review to a product. One review per user per product. Rate limited.
    """
    if user["user_id"] != review.user_id:
        raise Exception("You can only create a review as yourself.")
    return await review_controller.add_review(product_id, review, collection)

@router.patch("/{product_id}/reviews/{user_id}", response_model=Review, responses={403: {"model": ErrorResponseModel}, 404: {"model": ErrorResponseModel}})
async def update_review(product_id: str, user_id: str, review: Review, collection=Depends(get_product_collection), user=Depends(get_current_user)):
    """
    Update a review. Only the creator or admin can update.
    """
    return await review_controller.update_review(product_id, user_id, review, collection, user)

@router.delete("/{product_id}/reviews/{user_id}", status_code=status.HTTP_204_NO_CONTENT, responses={403: {"model": ErrorResponseModel}, 404: {"model": ErrorResponseModel}})
async def delete_review(product_id: str, user_id: str, collection=Depends(get_product_collection), user=Depends(get_current_user)):
    """
    Delete a review. Only the creator or admin can delete.
    """
    return await review_controller.delete_review(product_id, user_id, collection, user)

@router.post("/{product_id}/reviews/{user_id}/report", status_code=status.HTTP_201_CREATED, responses={404: {"model": ErrorResponseModel}, 429: {"description": "Rate limit exceeded"}})
@limiter.limit("10/minute")
async def report_review(product_id: str, user_id: str, report: ReviewReport, collection=Depends(get_product_collection), user=Depends(get_current_user), request: Request = None):
    """
    Report a review for abuse. Rate limited.
    """
    report.reported_by = user["user_id"]
    return await review_controller.report_review(product_id, user_id, report, collection, user)
