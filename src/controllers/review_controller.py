from datetime import datetime
from bson import ObjectId
from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.models.review import Review, ReviewReport

async def list_reviews(product_id, collection):
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)
    return doc.get("reviews", [])

async def add_review(product_id, review: Review, collection):
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)
    reviews = doc.get("reviews", [])
    for r in reviews:
        if r["user_id"] == review.user_id:
            raise ErrorResponse("User has already reviewed this product", status_code=400)
    reviews.append(review.dict())
    ratings = [r["rating"] for r in reviews]
    average_rating = sum(ratings) / len(ratings)
    num_reviews = len(reviews)
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"reviews": reviews, "average_rating": average_rating, "num_reviews": num_reviews, "updated_at": datetime.utcnow()}}
    )
    logger.info(f"Added review for product {product_id} by user {review.user_id}", extra={"event": "add_review", "product_id": product_id, "user_id": review.user_id})
    return review

async def update_review(product_id, user_id, review: Review, collection, acting_user):
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)
    reviews = doc.get("reviews", [])
    found = False
    for r in reviews:
        if r["user_id"] == user_id:
            if acting_user["user_id"] != user_id and "admin" not in acting_user.get("roles", []):
                raise ErrorResponse("You can only update your own review unless you are an admin.", status_code=403)
            r.update(review.dict(exclude_unset=True))
            r["updated_at"] = datetime.utcnow().isoformat()
            r["updated_by"] = acting_user["user_id"]
            found = True
            break
    if not found:
        raise ErrorResponse("Review not found for this user", status_code=404)
    ratings = [r["rating"] for r in reviews]
    average_rating = sum(ratings) / len(ratings) if ratings else 0
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"reviews": reviews, "average_rating": average_rating, "updated_at": datetime.utcnow()}}
    )
    logger.info(f"Updated review for product {product_id} by user {user_id}", extra={"event": "update_review", "product_id": product_id, "user_id": user_id})
    return review

async def delete_review(product_id, user_id, collection, acting_user):
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)
    reviews = doc.get("reviews", [])
    review_to_delete = next((r for r in reviews if r["user_id"] == user_id), None)
    if not review_to_delete:
        raise ErrorResponse("Review not found for this user", status_code=404)
    if acting_user["user_id"] != user_id and "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("You can only delete your own review unless you are an admin.", status_code=403)
    new_reviews = [r for r in reviews if r["user_id"] != user_id]
    ratings = [r["rating"] for r in new_reviews]
    average_rating = sum(ratings) / len(ratings) if ratings else 0
    num_reviews = len(new_reviews)
    await collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"reviews": new_reviews, "average_rating": average_rating, "num_reviews": num_reviews, "updated_at": datetime.utcnow()}}
    )
    logger.info(f"Deleted review for product {product_id} by user {user_id}", extra={"event": "delete_review", "product_id": product_id, "user_id": user_id})
    return None

async def report_review(product_id, user_id, report: ReviewReport, collection, acting_user):
    doc = await collection.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise ErrorResponse("Product not found", status_code=404)
    reviews = doc.get("reviews", [])
    for r in reviews:
        if r["user_id"] == user_id:
            r.setdefault("reports", []).append(report.dict())
            await collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"reviews": reviews, "updated_at": datetime.utcnow()}}
            )
            logger.info(f"Reported review for product {product_id} by user {user_id}", extra={"event": "report_review", "product_id": product_id, "user_id": user_id, "reported_by": report.reported_by})
            return {"message": "Review reported"}
    raise ErrorResponse("Review not found for this user", status_code=404)
