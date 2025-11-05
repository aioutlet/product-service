"""
Badge Service - Business logic for badge management.

This service handles:
- Manual badge assignment/removal
- Automated badge rule evaluation
- Badge priority and display logic
- Badge lifecycle management (expiration)
- Badge statistics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from src.models.badge import (
    BadgeType, BadgePriority, Badge, BadgeRule, BadgeRuleCondition,
    BadgeEvaluationResult, BadgeStatistics
)


class BadgeService:
    """Service for managing product badges."""

    def __init__(self, product_repository):
        """
        Initialize badge service.
        
        Args:
            product_repository: Repository for product data access
        """
        self.product_repository = product_repository

    # Predefined badge rules (can be moved to database later)
    DEFAULT_BADGE_RULES = [
        BadgeRule(
            badgeType=BadgeType.NEW,
            name="New Product Rule",
            description="Products created within last 30 days",
            conditions=[
                BadgeRuleCondition(
                    field="createdAt",
                    operator=">=",
                    value="30_days_ago"
                )
            ],
            requiresAllConditions=True,
            isActive=True,
            priority=10,
            autoRemoveWhenInvalid=True
        ),
        BadgeRule(
            badgeType=BadgeType.BEST_SELLER,
            name="Best Seller Rule",
            description="Products with 1000+ sales in last 30 days",
            conditions=[
                BadgeRuleCondition(
                    field="salesMetrics.last30Days.units",
                    operator=">=",
                    value=1000
                )
            ],
            requiresAllConditions=True,
            isActive=True,
            priority=20,
            autoRemoveWhenInvalid=True
        ),
        BadgeRule(
            badgeType=BadgeType.TRENDING,
            name="Trending Product Rule",
            description="Products with 50+ sales and 500+ views in last 7 days",
            conditions=[
                BadgeRuleCondition(
                    field="salesMetrics.last7Days.units",
                    operator=">=",
                    value=50
                ),
                BadgeRuleCondition(
                    field="viewMetrics.last7Days.views",
                    operator=">=",
                    value=500
                )
            ],
            requiresAllConditions=True,
            isActive=True,
            priority=15,
            autoRemoveWhenInvalid=True
        ),
        BadgeRule(
            badgeType=BadgeType.LOW_STOCK,
            name="Low Stock Rule",
            description="Products with less than 10 units in stock",
            conditions=[
                BadgeRuleCondition(
                    field="availabilityStatus.quantity",
                    operator="<=",
                    value=10
                ),
                BadgeRuleCondition(
                    field="availabilityStatus.quantity",
                    operator=">",
                    value=0
                )
            ],
            requiresAllConditions=True,
            isActive=True,
            priority=25,
            autoRemoveWhenInvalid=True
        )
    ]

    async def assign_badge(
        self,
        product_id: str,
        badge_type: BadgeType,
        assigned_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manually assign a badge to a product.
        
        Args:
            product_id: Product ID
            badge_type: Type of badge to assign
            assigned_by: User ID who assigned the badge (None for automated)
            expires_at: Optional expiration date
            metadata: Additional badge metadata
            
        Returns:
            Updated product with badge
            
        Raises:
            ValueError: If product not found or badge already exists
        """
        # Get product
        product = await self.product_repository.find_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Check if badge already exists
        if "badges" not in product:
            product["badges"] = []

        for badge in product["badges"]:
            if badge.get("type") == badge_type.value:
                raise ValueError(f"Badge {badge_type.value} already assigned to product {product_id}")

        # Create new badge
        new_badge = Badge(
            type=badge_type,
            assignedAt=datetime.utcnow(),
            assignedBy=assigned_by,
            expiresAt=expires_at,
            metadata=metadata or {}
        )

        # Add badge to product
        product["badges"].append(new_badge.model_dump())

        # Update product
        update_result = await self.product_repository.update(
            product_id,
            {"badges": product["badges"]}
        )

        if not update_result:
            raise ValueError(f"Failed to update product {product_id}")

        return await self.product_repository.find_by_id(product_id)

    async def remove_badge(
        self,
        product_id: str,
        badge_type: BadgeType
    ) -> Dict[str, Any]:
        """
        Remove a badge from a product.
        
        Args:
            product_id: Product ID
            badge_type: Type of badge to remove
            
        Returns:
            Updated product without badge
            
        Raises:
            ValueError: If product not found or badge doesn't exist
        """
        # Get product
        product = await self.product_repository.find_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Check if product has badges
        if "badges" not in product or not product["badges"]:
            raise ValueError(f"Product {product_id} has no badges")

        # Find and remove badge
        original_count = len(product["badges"])
        product["badges"] = [
            badge for badge in product["badges"]
            if badge.get("type") != badge_type.value
        ]

        if len(product["badges"]) == original_count:
            raise ValueError(f"Badge {badge_type.value} not found on product {product_id}")

        # Update product
        update_result = await self.product_repository.update(
            product_id,
            {"badges": product["badges"]}
        )

        if not update_result:
            raise ValueError(f"Failed to update product {product_id}")

        return await self.product_repository.find_by_id(product_id)

    async def bulk_assign_badge(
        self,
        product_ids: List[str],
        badge_type: BadgeType,
        assigned_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assign a badge to multiple products.
        
        Args:
            product_ids: List of product IDs
            badge_type: Type of badge to assign
            assigned_by: User ID who assigned the badge
            expires_at: Optional expiration date
            metadata: Additional badge metadata
            
        Returns:
            Summary of assignment results
        """
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        for product_id in product_ids:
            try:
                await self.assign_badge(
                    product_id=product_id,
                    badge_type=badge_type,
                    assigned_by=assigned_by,
                    expires_at=expires_at,
                    metadata=metadata
                )
                results["success"].append(product_id)
            except ValueError as e:
                if "already assigned" in str(e):
                    results["skipped"].append({"productId": product_id, "reason": str(e)})
                else:
                    results["failed"].append({"productId": product_id, "error": str(e)})
            except Exception as e:
                results["failed"].append({"productId": product_id, "error": str(e)})

        return {
            "totalProcessed": len(product_ids),
            "successCount": len(results["success"]),
            "failedCount": len(results["failed"]),
            "skippedCount": len(results["skipped"]),
            "results": results
        }

    async def get_product_badges(self, product_id: str) -> Dict[str, Any]:
        """
        Get all badges for a product with display priority.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product badges with display badge
            
        Raises:
            ValueError: If product not found
        """
        product = await self.product_repository.find_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        badges = product.get("badges", [])
        
        # Remove expired badges
        now = datetime.utcnow()
        active_badges = []
        for badge in badges:
            expires_at = badge.get("expiresAt")
            if expires_at is None or (isinstance(expires_at, datetime) and expires_at > now):
                active_badges.append(badge)

        # Get display badge (highest priority)
        display_badge = self._get_display_badge(active_badges)

        return {
            "productId": product_id,
            "badges": active_badges,
            "displayBadge": display_badge
        }

    def _get_display_badge(self, badges: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Get the highest priority badge for display.
        
        Args:
            badges: List of badge dictionaries
            
        Returns:
            Badge with highest priority or None
        """
        if not badges:
            return None

        # Sort by priority (highest first)
        sorted_badges = sorted(
            badges,
            key=lambda b: BadgePriority[b["type"].upper()].value,
            reverse=True
        )

        return sorted_badges[0] if sorted_badges else None

    async def evaluate_badge_rules(
        self,
        product_ids: Optional[List[str]] = None,
        badge_types: Optional[List[BadgeType]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate automated badge rules for products.
        
        Args:
            product_ids: Specific product IDs to evaluate (None = all active products)
            badge_types: Specific badge types to evaluate (None = all types)
            dry_run: If True, don't apply changes
            
        Returns:
            Evaluation results with summary
        """
        # Get products to evaluate
        if product_ids:
            products = []
            for pid in product_ids:
                product = await self.product_repository.find_by_id(pid)
                if product and product.get("status") == "active":
                    products.append(product)
        else:
            # Get all active products
            products = await self.product_repository.find_many({"status": "active"})

        # Filter rules by badge types
        rules = self.DEFAULT_BADGE_RULES
        if badge_types:
            rules = [r for r in rules if r.badgeType in badge_types and r.isActive]
        else:
            rules = [r for r in rules if r.isActive]

        # Evaluate each product
        results = []
        total_added = 0
        total_removed = 0
        total_errors = 0

        for product in products:
            result = await self._evaluate_product_rules(product, rules, dry_run)
            results.append(result)
            total_added += len(result.badgesAdded)
            total_removed += len(result.badgesRemoved)
            total_errors += len(result.errors)

        return {
            "success": total_errors == 0,
            "productsEvaluated": len(products),
            "results": [r.model_dump() for r in results],
            "summary": {
                "badgesAdded": total_added,
                "badgesRemoved": total_removed,
                "errors": total_errors
            }
        }

    async def _evaluate_product_rules(
        self,
        product: Dict[str, Any],
        rules: List[BadgeRule],
        dry_run: bool
    ) -> BadgeEvaluationResult:
        """
        Evaluate badge rules for a single product.
        
        Args:
            product: Product document
            rules: List of badge rules to evaluate
            dry_run: If True, don't apply changes
            
        Returns:
            Evaluation result for the product
        """
        product_id = str(product["_id"])
        badges_added = []
        badges_removed = []
        errors = []

        current_badges = product.get("badges", [])
        current_badge_types = {b.get("type") for b in current_badges}

        for rule in rules:
            try:
                # Check if conditions are met
                conditions_met = self._evaluate_conditions(product, rule)

                badge_type_str = rule.badgeType.value

                if conditions_met:
                    # Add badge if not already present and not manually assigned
                    if badge_type_str not in current_badge_types:
                        if not dry_run:
                            await self.assign_badge(
                                product_id=product_id,
                                badge_type=rule.badgeType,
                                assigned_by=None,  # Automated
                                expires_at=None,
                                metadata={"rule": rule.name}
                            )
                        badges_added.append(rule.badgeType)
                else:
                    # Remove badge if present and auto-remove is enabled
                    if badge_type_str in current_badge_types and rule.autoRemoveWhenInvalid:
                        # Check if badge was automated (assignedBy is None)
                        badge = next((b for b in current_badges if b.get("type") == badge_type_str), None)
                        if badge and badge.get("assignedBy") is None:
                            if not dry_run:
                                await self.remove_badge(
                                    product_id=product_id,
                                    badge_type=rule.badgeType
                                )
                            badges_removed.append(rule.badgeType)

            except Exception as e:
                errors.append(f"Error evaluating rule {rule.name}: {str(e)}")

        return BadgeEvaluationResult(
            productId=product_id,
            badgesAdded=badges_added,
            badgesRemoved=badges_removed,
            errors=errors
        )

    def _evaluate_conditions(self, product: Dict[str, Any], rule: BadgeRule) -> bool:
        """
        Evaluate if product meets rule conditions.
        
        Args:
            product: Product document
            rule: Badge rule with conditions
            
        Returns:
            True if conditions are met
        """
        results = []

        for condition in rule.conditions:
            result = self._evaluate_condition(product, condition)
            results.append(result)

        # Apply AND/OR logic
        if rule.requiresAllConditions:
            return all(results)
        else:
            return any(results)

    def _evaluate_condition(
        self,
        product: Dict[str, Any],
        condition: BadgeRuleCondition
    ) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            product: Product document
            condition: Condition to evaluate
            
        Returns:
            True if condition is met
        """
        # Get field value from product (support nested fields)
        value = self._get_nested_field(product, condition.field)

        # Handle special values
        if condition.value == "30_days_ago":
            from datetime import timedelta
            threshold = datetime.utcnow() - timedelta(days=30)
            condition_value = threshold
        else:
            condition_value = condition.value

        # Evaluate operator
        if value is None:
            return False

        try:
            if condition.operator == ">=":
                return value >= condition_value
            elif condition.operator == "<=":
                return value <= condition_value
            elif condition.operator == ">":
                return value > condition_value
            elif condition.operator == "<":
                return value < condition_value
            elif condition.operator == "==":
                return value == condition_value
            elif condition.operator == "!=":
                return value != condition_value
            elif condition.operator == "between":
                return condition_value[0] <= value <= condition_value[1]
            elif condition.operator == "in":
                return value in condition_value
            elif condition.operator == "not_in":
                return value not in condition_value
            else:
                return False
        except (TypeError, IndexError):
            return False

    def _get_nested_field(self, obj: Dict[str, Any], field_path: str) -> Any:
        """
        Get nested field value from object.
        
        Args:
            obj: Dictionary object
            field_path: Dot-separated field path (e.g., "salesMetrics.last30Days.units")
            
        Returns:
            Field value or None if not found
        """
        parts = field_path.split(".")
        current = obj

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current

    async def remove_expired_badges(self) -> Dict[str, Any]:
        """
        Remove expired badges from all products.
        
        Returns:
            Summary of removed badges
        """
        now = datetime.utcnow()
        
        # Find all products with badges
        products = await self.product_repository.find_many({"badges": {"$exists": True, "$ne": []}})

        removed_count = 0
        updated_products = []

        for product in products:
            badges = product.get("badges", [])
            original_count = len(badges)

            # Filter out expired badges
            active_badges = []
            for badge in badges:
                expires_at = badge.get("expiresAt")
                if expires_at is None or (isinstance(expires_at, datetime) and expires_at > now):
                    active_badges.append(badge)

            # Update if badges were removed
            if len(active_badges) < original_count:
                product_id = str(product["_id"])
                await self.product_repository.update(
                    product_id,
                    {"badges": active_badges}
                )
                removed_count += original_count - len(active_badges)
                updated_products.append(product_id)

        return {
            "success": True,
            "badgesRemoved": removed_count,
            "productsUpdated": len(updated_products),
            "productIds": updated_products
        }

    async def get_badge_statistics(self) -> BadgeStatistics:
        """
        Get statistics about badge usage.
        
        Returns:
            Badge statistics
        """
        # Get all products with badges
        products = await self.product_repository.find_many({"badges": {"$exists": True, "$ne": []}})

        total_badges = 0
        badges_by_type: Dict[str, int] = {}
        automated_badges = 0
        manual_badges = 0
        expired_badges = 0
        now = datetime.utcnow()

        for product in products:
            badges = product.get("badges", [])
            total_badges += len(badges)

            for badge in badges:
                # Count by type
                badge_type = badge.get("type", "unknown")
                badges_by_type[badge_type] = badges_by_type.get(badge_type, 0) + 1

                # Count automated vs manual
                if badge.get("assignedBy") is None:
                    automated_badges += 1
                else:
                    manual_badges += 1

                # Count expired
                expires_at = badge.get("expiresAt")
                if expires_at and isinstance(expires_at, datetime) and expires_at <= now:
                    expired_badges += 1

        return BadgeStatistics(
            totalBadges=total_badges,
            badgesByType=badges_by_type,
            productsWithBadges=len(products),
            automatedBadges=automated_badges,
            manualBadges=manual_badges,
            expiredBadges=expired_badges
        )
