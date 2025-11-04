"""
Badge Manager Service
Handles automated badge assignment based on sales/analytics metrics.
Implements PRD REQ-3.2.3: Sales Metrics & Badge Automation
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.db.mongodb import get_product_collection
from src.services.dapr_publisher import get_dapr_publisher
from src.observability.logging import logger


async def evaluate_badge_criteria(
    product_id: str,
    badge_type: str,
    metrics: Dict[str, Any],
    criteria_threshold: Any,
    correlation_id: Optional[str] = None
):
    """
    Evaluate badge assignment criteria and auto-assign/remove badges.
    
    Args:
        product_id: Product ID to evaluate
        badge_type: Type of badge (best-seller, trending, hot-deal)
        metrics: Current metrics for evaluation
        criteria_threshold: Threshold value for badge assignment
        correlation_id: Correlation ID for tracing
        
    Implements:
        - REQ-3.2.3: Automated badge assignment
        - Best Seller: Top 100 in category by sales
        - Trending: Views increased by 50%+ in last 7 days
        - Hot Deal: Conversion rate > category avg + 20%
    """
    try:
        collection = await get_product_collection()
        publisher = get_dapr_publisher()
        
        # Find the product
        product = await collection.find_one({"_id": product_id})
        if not product:
            logger.warning(
                f"Product not found for badge evaluation: {product_id}",
                metadata={
                    'event': 'badge_eval_product_not_found',
                    'productId': product_id,
                    'correlationId': correlation_id
                }
            )
            return
        
        # Get current badges
        current_badges = product.get('badges', [])
        has_badge = any(b.get('badge_type') == badge_type for b in current_badges)
        
        # Evaluate criteria based on badge type
        should_have_badge = False
        
        if badge_type == 'best-seller':
            # Top 100 in category
            category_rank = metrics.get('categoryRank', 999)
            should_have_badge = category_rank <= criteria_threshold
            
        elif badge_type == 'trending':
            # Views increased by 50%+
            view_growth_pct = metrics.get('viewGrowthPercent', 0)
            should_have_badge = view_growth_pct >= 50
            
        elif badge_type == 'hot-deal':
            # Conversion rate > category avg + 20%
            conversion_rate = metrics.get('conversionRate', 0)
            category_avg = metrics.get('categoryAvgConversion', 0)
            should_have_badge = conversion_rate > (category_avg + 0.20)
        
        # Handle badge assignment/removal
        if should_have_badge and not has_badge:
            # Add new badge
            new_badge = {
                'badge_type': badge_type,
                'assigned_at': datetime.now(timezone.utc),
                'expires_at': None,
                'auto_assigned': True,
                'criteria': metrics
            }
            
            current_badges.append(new_badge)
            
            await collection.update_one(
                {"_id": product_id},
                {"$set": {"badges": current_badges}},
                upsert=False
            )
            
            # Publish badge.auto.assigned event
            await publisher.publish(
                'product.badge.auto.assigned',
                {
                    'productId': product_id,
                    'badgeType': badge_type,
                    'assignedAt': new_badge['assigned_at'].isoformat(),
                    'criteria': metrics
                },
                correlation_id
            )
            
            logger.info(
                f"Auto-assigned {badge_type} badge to product {product_id}",
                metadata={
                    'event': 'badge_auto_assigned',
                    'productId': product_id,
                    'badgeType': badge_type,
                    'metrics': metrics,
                    'correlationId': correlation_id
                }
            )
            
        elif not should_have_badge and has_badge:
            # Remove badge
            current_badges = [
                b for b in current_badges
                if b.get('badge_type') != badge_type
            ]

            await collection.update_one(
                {"_id": product_id},
                {"$set": {"badges": current_badges}},
                upsert=False
            )
            
            # Publish badge.auto.removed event
            await publisher.publish(
                'product.badge.auto.removed',
                {
                    'productId': product_id,
                    'badgeType': badge_type,
                    'removedAt': datetime.now(timezone.utc).isoformat(),
                    'criteria': metrics
                },
                correlation_id
            )
            
            logger.info(
                f"Auto-removed {badge_type} badge from product {product_id}",
                metadata={
                    'event': 'badge_auto_removed',
                    'productId': product_id,
                    'badgeType': badge_type,
                    'metrics': metrics,
                    'correlationId': correlation_id
                }
            )
        
    except Exception as e:
        logger.error(
            f"Failed to evaluate badge criteria: {str(e)}",
            metadata={
                'event': 'badge_eval_error',
                'productId': product_id,
                'badgeType': badge_type,
                'error': str(e),
                'errorType': type(e).__name__,
                'correlationId': correlation_id
            }
        )
        raise
