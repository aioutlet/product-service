from datetime import datetime

from bson import ObjectId

from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.models.review import Review, ReviewReport


async def list_reviews(product_id, collection):
    """
    Get all reviews for a specific product.

    Args:
        product_id: Product ID to get reviews for
        collection: MongoDB collection instance

    Returns:
        list: List of reviews for the product

    Raises:
        ErrorResponse: If product not found
    """
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)
    return doc.get("reviews", [])


async def add_review(product_id, review: Review, collection):
    """
    Add a new review to a product.

    Args:
        product_id: Product ID to add review to
        review: Review object containing review data
        collection: MongoDB collection instance

    Returns:
        Review: The added review object

    Raises:
        ErrorResponse: If product not found or user has already reviewed
    """
    # Check if product exists
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)

    # Get existing reviews and check for duplicates
    reviews = doc.get("reviews", [])
    for r in reviews:
        if r["user_id"] == review.user_id:
            raise ErrorResponse(
                "User has already reviewed this product", status_code=400
            )

    # Add new review
    reviews.append(review.dict())

    # Recalculate average rating and review count
    ratings = [r["rating"] for r in reviews]
    average_rating = sum(ratings) / len(ratings)
    num_reviews = len(reviews)

    # Update product with new review data
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "reviews": reviews,
                "average_rating": average_rating,
                "num_reviews": num_reviews,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Log successful review addition
    logger.info(
        f"Added review for product {product_id} by user {review.user_id}",
        extra={
            "event": "add_review",
            "product_id": product_id,
            "user_id": review.user_id,
        },
    )
    return review


async def update_review(product_id, user_id, review: Review, collection, acting_user):
    """
    Update an existing review for a product.

    Args:
        product_id: Product ID containing the review
        user_id: User ID of the review author
        review: Review object with updated data
        collection: MongoDB collection instance
        acting_user: User performing the operation

    Returns:
        Review: The updated review object

    Raises:
        ErrorResponse: If product/review not found or permission denied
    """
    # Check if product exists
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)

    # Find and update the review
    reviews = doc.get("reviews", [])
    found = False
    for r in reviews:
        if r["user_id"] == user_id:
            # Check permissions - user can only update their own review unless admin
            if acting_user["user_id"] != user_id and "admin" not in acting_user.get(
                "roles", []
            ):
                raise ErrorResponse(
                    "You can only update your own review unless you are an admin.",
                    status_code=403,
                )

            # Update review with new data
            r.update(review.dict(exclude_unset=True))
            r["updated_at"] = datetime.utcnow().isoformat()
            r["updated_by"] = acting_user["user_id"]
            found = True
            break

    if not found:
        raise ErrorResponse("Review not found for this user", status_code=404)

    # Recalculate average rating
    ratings = [r["rating"] for r in reviews]
    average_rating = sum(ratings) / len(ratings) if ratings else 0

    # Update product with modified review data
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "reviews": reviews,
                "average_rating": average_rating,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Log successful review update
    logger.info(
        f"Updated review for product {product_id} by user {user_id}",
        extra={"event": "update_review", "product_id": product_id, "user_id": user_id},
    )
    return review


async def delete_review(product_id, user_id, collection, acting_user):
    """
    Delete a review from a product.

    Args:
        product_id: Product ID containing the review
        user_id: User ID of the review author
        collection: MongoDB collection instance
        acting_user: User performing the operation

    Returns:
        None

    Raises:
        ErrorResponse: If product/review not found or permission denied
    """
    # Check if product exists
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)

    # Find the review to delete
    reviews = doc.get("reviews", [])
    review_to_delete = next((r for r in reviews if r["user_id"] == user_id), None)
    if not review_to_delete:
        raise ErrorResponse("Review not found for this user", status_code=404)

    # Check permissions - user can only delete their own review unless admin
    if acting_user["user_id"] != user_id and "admin" not in acting_user.get(
        "roles", []
    ):
        raise ErrorResponse(
            "You can only delete your own review unless you are an admin.",
            status_code=403,
        )

    # Remove the review
    new_reviews = [r for r in reviews if r["user_id"] != user_id]

    # Recalculate rating and count
    ratings = [r["rating"] for r in new_reviews]
    average_rating = sum(ratings) / len(ratings) if ratings else 0
    num_reviews = len(new_reviews)

    # Update product with modified review data
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "reviews": new_reviews,
                "average_rating": average_rating,
                "num_reviews": num_reviews,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Log successful review deletion
    logger.info(
        f"Deleted review for product {product_id} by user {user_id}",
        extra={"event": "delete_review", "product_id": product_id, "user_id": user_id},
    )
    return None


async def report_review(
    product_id, user_id, report: ReviewReport, collection, acting_user
):
    """
    Report a review as inappropriate or spam.

    Args:
        product_id: Product ID containing the review
        user_id: User ID of the review author being reported
        report: ReviewReport object containing report details
        collection: MongoDB collection instance
        acting_user: User making the report

    Returns:
        dict: Success message

    Raises:
        ErrorResponse: If product/review not found
    """
    # Check if product exists
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)

    # Find the review to report
    reviews = doc.get("reviews", [])
    for r in reviews:
        if r["user_id"] == user_id:
            # Add report to review
            r.setdefault("reports", []).append(report.dict())

            # Update product with report data
            await collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"reviews": reviews, "updated_at": datetime.utcnow()}},
            )

            # Log successful report
            logger.info(
                f"Reported review for product {product_id} by user {user_id}",
                extra={
                    "event": "report_review",
                    "product_id": product_id,
                    "user_id": user_id,
                    "reported_by": report.reported_by,
                },
            )
            return {"message": "Review reported"}

    raise ErrorResponse("Review not found for this user", status_code=404)
