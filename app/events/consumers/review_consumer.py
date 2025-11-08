"""
Dapr Event Consumer for Product Service
Handles incoming events from other services via Dapr pub/sub
"""

from typing import Dict, Any
from datetime import datetime

from app.core.logger import logger
from app.repositories.product import ProductRepository


class ReviewEventConsumer:
    """
    Consumer for handling review-related events.
    Updates product review aggregates when reviews are created, updated, or deleted.
    """
    
    def __init__(self):
        self.db = None
        self.product_repo = None
    
    async def initialize(self):
        """Initialize database connection and repository"""
        if not self.db:
            # Lazy import to avoid circular dependency
            from app.db.mongodb import get_database
            self.db = await get_database()
            self.product_repo = ProductRepository(self.db)
    
    async def handle_review_created(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle review.created event.
        Updates product review aggregates with new review data.
        
        Args:
            event_data: CloudEvents formatted event data
            
        Returns:
            Response dict with status
        """
        try:
            await self.initialize()
            
            # Extract event metadata
            correlation_id = event_data.get("correlationId", "no-correlation")
            data = event_data.get("data", {})
            
            # Extract review data
            product_id = data.get("productId")
            review_id = data.get("reviewId")
            rating = data.get("rating")
            verified = data.get("verified", False)
            created_at = data.get("createdAt")
            
            if not product_id or not review_id or rating is None:
                logger.warning(
                    "Invalid review.created event - missing required fields",
                    metadata={
                        "correlationId": correlation_id,
                        "eventType": "review.created",
                        "productId": product_id,
                        "reviewId": review_id
                    }
                )
                return {"status": "error", "message": "Missing required fields"}
            
            logger.info(
                f"Processing review.created event for product {product_id}",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "reviewId": review_id,
                    "rating": rating
                }
            )
            
            # Get current product
            product = await self.product_repo.get_by_id(product_id)
            if not product:
                logger.warning(
                    f"Product not found: {product_id}",
                    metadata={
                        "correlationId": correlation_id,
                        "productId": product_id,
                        "reviewId": review_id
                    }
                )
                return {"status": "error", "message": "Product not found"}
            
            # Calculate new aggregates
            current_aggregates = product.get("review_aggregates", {})
            
            # Get current values with defaults
            total_count = current_aggregates.get("total_review_count", 0)
            verified_count = current_aggregates.get("verified_review_count", 0)
            current_avg = current_aggregates.get("average_rating", 0.0)
            rating_dist = current_aggregates.get("rating_distribution", {
                "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
            })
            recent_reviews = current_aggregates.get("recent_reviews", [])
            
            # Update counts
            new_total_count = total_count + 1
            if verified:
                new_verified_count = verified_count + 1
            else:
                new_verified_count = verified_count
            
            # Recalculate average rating
            # Formula: new_avg = (current_avg * total_count + new_rating) / (total_count + 1)
            new_average = ((current_avg * total_count) + rating) / new_total_count
            new_average = round(new_average, 2)
            
            # Update rating distribution
            rating_key = str(rating)
            if rating_key in rating_dist:
                rating_dist[rating_key] += 1
            
            # Update recent reviews list (keep last 5)
            recent_reviews = [review_id] + recent_reviews[:4]
            
            # Build updated aggregates
            updated_aggregates = {
                "average_rating": new_average,
                "total_review_count": new_total_count,
                "verified_review_count": new_verified_count,
                "rating_distribution": rating_dist,
                "recent_reviews": recent_reviews,
                "last_review_date": created_at,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
            # Update product in database
            await self.product_repo.update(
                product_id,
                {"review_aggregates": updated_aggregates}
            )
            
            logger.info(
                f"Updated review aggregates for product {product_id}",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "reviewId": review_id,
                    "newAverageRating": new_average,
                    "newTotalCount": new_total_count
                }
            )
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(
                f"Error processing review.created event: {str(e)}",
                metadata={
                    "correlationId": event_data.get("correlationId", "no-correlation"),
                    "error": str(e),
                    "eventType": "review.created"
                }
            )
            # Return success to avoid retries for now
            # In production, you might want to implement retry logic or dead letter queue
            return {"status": "error", "message": str(e)}
    
    async def handle_review_updated(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle review.updated event.
        Recalculates review aggregates when a review rating changes.
        
        Args:
            event_data: CloudEvents formatted event data
            
        Returns:
            Response dict with status
        """
        try:
            await self.initialize()
            
            correlation_id = event_data.get("correlationId", "no-correlation")
            data = event_data.get("data", {})
            
            product_id = data.get("productId")
            review_id = data.get("reviewId")
            new_rating = data.get("rating")
            old_rating = data.get("previousRating")
            
            if not product_id or new_rating is None or old_rating is None:
                logger.warning(
                    "Invalid review.updated event - missing required fields",
                    metadata={"correlationId": correlation_id}
                )
                return {"status": "error", "message": "Missing required fields"}
            
            # Only process if rating actually changed
            if new_rating == old_rating:
                return {"status": "success", "message": "Rating unchanged"}
            
            logger.info(
                f"Processing review.updated event for product {product_id}",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "reviewId": review_id,
                    "oldRating": old_rating,
                    "newRating": new_rating
                }
            )
            
            # Get current product
            product = await self.product_repo.get_by_id(product_id)
            if not product:
                return {"status": "error", "message": "Product not found"}
            
            current_aggregates = product.get("review_aggregates", {})
            total_count = current_aggregates.get("total_review_count", 0)
            current_avg = current_aggregates.get("average_rating", 0.0)
            rating_dist = current_aggregates.get("rating_distribution", {
                "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
            })
            
            # Recalculate average: remove old rating, add new rating
            # new_avg = (current_avg * total_count - old_rating + new_rating) / total_count
            new_average = ((current_avg * total_count) - old_rating + new_rating) / total_count
            new_average = round(new_average, 2)
            
            # Update rating distribution
            old_key = str(old_rating)
            new_key = str(new_rating)
            if old_key in rating_dist:
                rating_dist[old_key] = max(0, rating_dist[old_key] - 1)
            if new_key in rating_dist:
                rating_dist[new_key] += 1
            
            # Update aggregates
            updated_aggregates = current_aggregates.copy()
            updated_aggregates.update({
                "average_rating": new_average,
                "rating_distribution": rating_dist,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            })
            
            await self.product_repo.update(
                product_id,
                {"review_aggregates": updated_aggregates}
            )
            
            logger.info(
                f"Updated review aggregates for product {product_id} (review updated)",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "newAverageRating": new_average
                }
            )
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(
                f"Error processing review.updated event: {str(e)}",
                metadata={
                    "correlationId": event_data.get("correlationId", "no-correlation"),
                    "error": str(e)
                }
            )
            return {"status": "error", "message": str(e)}
    
    async def handle_review_deleted(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Handle review.deleted event.
        Updates aggregates when a review is removed.
        
        Args:
            event_data: CloudEvents formatted event data
            
        Returns:
            Response dict with status
        """
        try:
            await self.initialize()
            
            correlation_id = event_data.get("correlationId", "no-correlation")
            data = event_data.get("data", {})
            
            product_id = data.get("productId")
            review_id = data.get("reviewId")
            rating = data.get("rating")
            verified = data.get("verified", False)
            
            if not product_id or rating is None:
                return {"status": "error", "message": "Missing required fields"}
            
            logger.info(
                f"Processing review.deleted event for product {product_id}",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "reviewId": review_id
                }
            )
            
            product = await self.product_repo.get_by_id(product_id)
            if not product:
                return {"status": "error", "message": "Product not found"}
            
            current_aggregates = product.get("review_aggregates", {})
            total_count = current_aggregates.get("total_review_count", 0)
            verified_count = current_aggregates.get("verified_review_count", 0)
            current_avg = current_aggregates.get("average_rating", 0.0)
            rating_dist = current_aggregates.get("rating_distribution", {
                "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
            })
            recent_reviews = current_aggregates.get("recent_reviews", [])
            
            # Update counts
            new_total_count = max(0, total_count - 1)
            if verified:
                new_verified_count = max(0, verified_count - 1)
            else:
                new_verified_count = verified_count
            
            # Recalculate average
            if new_total_count > 0:
                new_average = ((current_avg * total_count) - rating) / new_total_count
                new_average = round(new_average, 2)
            else:
                new_average = 0.0
            
            # Update rating distribution
            rating_key = str(rating)
            if rating_key in rating_dist:
                rating_dist[rating_key] = max(0, rating_dist[rating_key] - 1)
            
            # Remove from recent reviews
            if review_id in recent_reviews:
                recent_reviews.remove(review_id)
            
            # Update aggregates
            updated_aggregates = {
                "average_rating": new_average,
                "total_review_count": new_total_count,
                "verified_review_count": new_verified_count,
                "rating_distribution": rating_dist,
                "recent_reviews": recent_reviews,
                "last_review_date": current_aggregates.get("last_review_date"),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
            await self.product_repo.update(
                product_id,
                {"review_aggregates": updated_aggregates}
            )
            
            logger.info(
                f"Updated review aggregates for product {product_id} (review deleted)",
                metadata={
                    "correlationId": correlation_id,
                    "productId": product_id,
                    "newAverageRating": new_average,
                    "newTotalCount": new_total_count
                }
            )
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(
                f"Error processing review.deleted event: {str(e)}",
                metadata={
                    "correlationId": event_data.get("correlationId", "no-correlation"),
                    "error": str(e)
                }
            )
            return {"status": "error", "message": str(e)}


# Global consumer instance
review_event_consumer = ReviewEventConsumer()
