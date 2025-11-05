"""
Unit tests for badge service.

Tests business logic for badge assignment, removal, rule evaluation, and statistics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.badge import BadgeType, Badge, BadgeRule, BadgeRuleCondition
from src.services.badge_service import BadgeService


@pytest.fixture
def mock_repository():
    """Create mock product repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def badge_service(mock_repository):
    """Create badge service with mock repository."""
    return BadgeService(mock_repository)


@pytest.fixture
def sample_product():
    """Create sample product document."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "name": "Test Product",
        "sku": "TEST-001",
        "status": "active",
        "price": 29.99,
        "badges": [],
        "salesMetrics": {
            "last30Days": {"units": 1200},
            "last7Days": {"units": 60}
        },
        "viewMetrics": {
            "last7Days": {"views": 600}
        },
        "availabilityStatus": {
            "quantity": 5
        },
        "createdAt": datetime.utcnow() - timedelta(days=20)
    }


class TestAssignBadge:
    """Tests for assign_badge method."""

    @pytest.mark.asyncio
    async def test_assign_badge_success(self, badge_service, mock_repository, sample_product):
        """Test successfully assigning a badge to a product."""
        # Setup
        updated_product = {**sample_product, "badges": [{"type": "sale"}]}
        mock_repository.find_by_id.side_effect = [sample_product, updated_product]
        mock_repository.update.return_value = True
        
        # Execute
        result = await badge_service.assign_badge(
            product_id="507f1f77bcf86cd799439011",
            badge_type=BadgeType.SALE,
            assigned_by="admin-123",
            metadata={"discount": 20}
        )
        
        # Assert
        assert mock_repository.find_by_id.called
        assert mock_repository.update.called
        assert result["badges"][0]["type"] == "sale"

    @pytest.mark.asyncio
    async def test_assign_badge_product_not_found(self, badge_service, mock_repository):
        """Test assigning badge fails when product not found."""
        # Setup
        mock_repository.find_by_id.return_value = None
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Product .* not found"):
            await badge_service.assign_badge(
                product_id="nonexistent",
                badge_type=BadgeType.SALE
            )

    @pytest.mark.asyncio
    async def test_assign_badge_already_exists(self, badge_service, mock_repository, sample_product):
        """Test assigning badge fails when badge already exists."""
        # Setup
        product_with_badge = {**sample_product, "badges": [{"type": "sale"}]}
        mock_repository.find_by_id.return_value = product_with_badge
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Badge .* already assigned"):
            await badge_service.assign_badge(
                product_id="507f1f77bcf86cd799439011",
                badge_type=BadgeType.SALE
            )

    @pytest.mark.asyncio
    async def test_assign_badge_with_expiration(self, badge_service, mock_repository, sample_product):
        """Test assigning badge with expiration date."""
        # Setup
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = True
        expires = datetime.utcnow() + timedelta(days=30)
        
        # Execute
        result = await badge_service.assign_badge(
            product_id="507f1f77bcf86cd799439011",
            badge_type=BadgeType.FEATURED,
            expires_at=expires
        )
        
        # Assert
        assert mock_repository.update.called


class TestRemoveBadge:
    """Tests for remove_badge method."""

    @pytest.mark.asyncio
    async def test_remove_badge_success(self, badge_service, mock_repository, sample_product):
        """Test successfully removing a badge from a product."""
        # Setup
        product_with_badge = {**sample_product, "badges": [{"type": "sale"}]}
        updated_product = {**sample_product, "badges": []}
        mock_repository.find_by_id.side_effect = [product_with_badge, updated_product]
        mock_repository.update.return_value = True
        
        # Execute
        result = await badge_service.remove_badge(
            product_id="507f1f77bcf86cd799439011",
            badge_type=BadgeType.SALE
        )
        
        # Assert
        assert mock_repository.update.called

    @pytest.mark.asyncio
    async def test_remove_badge_product_not_found(self, badge_service, mock_repository):
        """Test removing badge fails when product not found."""
        # Setup
        mock_repository.find_by_id.return_value = None
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Product .* not found"):
            await badge_service.remove_badge(
                product_id="nonexistent",
                badge_type=BadgeType.SALE
            )

    @pytest.mark.asyncio
    async def test_remove_badge_no_badges(self, badge_service, mock_repository, sample_product):
        """Test removing badge fails when product has no badges."""
        # Setup
        mock_repository.find_by_id.return_value = sample_product
        
        # Execute & Assert
        with pytest.raises(ValueError, match="has no badges"):
            await badge_service.remove_badge(
                product_id="507f1f77bcf86cd799439011",
                badge_type=BadgeType.SALE
            )

    @pytest.mark.asyncio
    async def test_remove_badge_not_found(self, badge_service, mock_repository, sample_product):
        """Test removing badge fails when badge doesn't exist."""
        # Setup
        product_with_badge = {**sample_product, "badges": [{"type": "featured"}]}
        mock_repository.find_by_id.return_value = product_with_badge
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Badge .* not found"):
            await badge_service.remove_badge(
                product_id="507f1f77bcf86cd799439011",
                badge_type=BadgeType.SALE
            )


class TestBulkAssignBadge:
    """Tests for bulk_assign_badge method."""

    @pytest.mark.asyncio
    async def test_bulk_assign_all_success(self, badge_service, mock_repository, sample_product):
        """Test bulk assigning badges to multiple products successfully."""
        # Setup - return fresh sample_product each time
        updated_product = {**sample_product, "badges": [{"type": "sale"}]}
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = True
        
        # We need to reset badges for each call
        async def mock_assign_side_effect(*args, **kwargs):
            # Return a copy with empty badges each time
            return {**sample_product, "badges": []}
        
        # Call assign_badge which internally calls find_by_id twice
        call_count = [0]
        def side_effect_find(*args):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return {**sample_product, "badges": []}
            else:
                return updated_product
        
        mock_repository.find_by_id.side_effect = side_effect_find
        
        # Execute
        result = await badge_service.bulk_assign_badge(
            product_ids=["id1", "id2", "id3"],
            badge_type=BadgeType.SALE,
            assigned_by="admin-123"
        )
        
        # Assert
        assert result["successCount"] == 3
        assert result["failedCount"] == 0
        assert result["skippedCount"] == 0

    @pytest.mark.asyncio
    async def test_bulk_assign_partial_success(self, badge_service, mock_repository, sample_product):
        """Test bulk assigning with some failures."""
        # Setup - create call counter that returns products in sequence
        # For id1 and id3: first call returns product, second returns updated
        # For id2: returns None (not found)
        call_sequence = []
        
        def mock_find_side_effect(product_id):
            call_count = len([c for c in call_sequence if c == product_id])
            call_sequence.append(product_id)
            
            if product_id == "id2":
                return None
            elif call_count == 0:
                # First call - return product with empty badges
                return {**sample_product, "_id": product_id, "badges": []}
            else:
                # Second call - return updated product
                return {**sample_product, "_id": product_id, "badges": [{"type": "sale"}]}
        
        mock_repository.find_by_id.side_effect = mock_find_side_effect
        mock_repository.update.return_value = True
        
        # Execute
        result = await badge_service.bulk_assign_badge(
            product_ids=["id1", "id2", "id3"],
            badge_type=BadgeType.SALE
        )
        
        # Assert
        assert result["successCount"] == 2
        assert result["failedCount"] == 1


class TestGetProductBadges:
    """Tests for get_product_badges method."""

    @pytest.mark.asyncio
    async def test_get_badges_no_badges(self, badge_service, mock_repository, sample_product):
        """Test getting badges for product with no badges."""
        # Setup
        mock_repository.find_by_id.return_value = sample_product
        
        # Execute
        result = await badge_service.get_product_badges("507f1f77bcf86cd799439011")
        
        # Assert
        assert result["productId"] == "507f1f77bcf86cd799439011"
        assert result["badges"] == []
        assert result["displayBadge"] is None

    @pytest.mark.asyncio
    async def test_get_badges_with_active_badges(self, badge_service, mock_repository, sample_product):
        """Test getting badges for product with active badges."""
        # Setup
        product_with_badges = {
            **sample_product,
            "badges": [
                {"type": "sale", "assignedAt": datetime.utcnow(), "assignedBy": "admin"},
                {"type": "best_seller", "assignedAt": datetime.utcnow(), "assignedBy": None}
            ]
        }
        mock_repository.find_by_id.return_value = product_with_badges
        
        # Execute
        result = await badge_service.get_product_badges("507f1f77bcf86cd799439011")
        
        # Assert
        assert len(result["badges"]) == 2
        assert result["displayBadge"] is not None

    @pytest.mark.asyncio
    async def test_get_badges_filters_expired(self, badge_service, mock_repository, sample_product):
        """Test getting badges filters out expired badges."""
        # Setup
        past = datetime.utcnow() - timedelta(days=1)
        product_with_badges = {
            **sample_product,
            "badges": [
                {"type": "sale", "assignedAt": datetime.utcnow(), "expiresAt": past},
                {"type": "featured", "assignedAt": datetime.utcnow(), "expiresAt": None}
            ]
        }
        mock_repository.find_by_id.return_value = product_with_badges
        
        # Execute
        result = await badge_service.get_product_badges("507f1f77bcf86cd799439011")
        
        # Assert
        assert len(result["badges"]) == 1
        assert result["badges"][0]["type"] == "featured"


class TestGetDisplayBadge:
    """Tests for _get_display_badge method."""

    def test_display_badge_empty_list(self, badge_service):
        """Test getting display badge from empty list."""
        result = badge_service._get_display_badge([])
        assert result is None

    def test_display_badge_single_badge(self, badge_service):
        """Test getting display badge from single badge."""
        badges = [{"type": "sale"}]
        result = badge_service._get_display_badge(badges)
        assert result["type"] == "sale"

    def test_display_badge_priority_order(self, badge_service):
        """Test display badge selects highest priority."""
        badges = [
            {"type": "new"},      # Priority 1
            {"type": "sale"},     # Priority 3
            {"type": "featured"}  # Priority 6 (highest)
        ]
        result = badge_service._get_display_badge(badges)
        assert result["type"] == "featured"


class TestEvaluateBadgeRules:
    """Tests for evaluate_badge_rules method."""

    @pytest.mark.asyncio
    async def test_evaluate_rules_all_products(self, badge_service, mock_repository, sample_product):
        """Test evaluating rules for all active products."""
        # Setup
        mock_repository.find_many.return_value = [sample_product]
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = True
        
        # Execute
        result = await badge_service.evaluate_badge_rules()
        
        # Assert
        assert result["success"]
        assert result["productsEvaluated"] == 1

    @pytest.mark.asyncio
    async def test_evaluate_rules_specific_products(self, badge_service, mock_repository, sample_product):
        """Test evaluating rules for specific products."""
        # Setup
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = True
        
        # Execute
        result = await badge_service.evaluate_badge_rules(
            product_ids=["507f1f77bcf86cd799439011"]
        )
        
        # Assert
        assert mock_repository.find_by_id.called

    @pytest.mark.asyncio
    async def test_evaluate_rules_dry_run(self, badge_service, mock_repository, sample_product):
        """Test evaluating rules in dry run mode."""
        # Setup
        mock_repository.find_many.return_value = [sample_product]
        
        # Execute
        result = await badge_service.evaluate_badge_rules(dry_run=True)
        
        # Assert
        assert not mock_repository.update.called


class TestEvaluateConditions:
    """Tests for _evaluate_conditions method."""

    def test_evaluate_conditions_all_met(self, badge_service, sample_product):
        """Test evaluating conditions when all are met."""
        rule = BadgeRule(
            badgeType=BadgeType.BEST_SELLER,
            name="Test",
            description="Test",
            conditions=[
                BadgeRuleCondition(field="salesMetrics.last30Days.units", operator=">=", value=1000),
                BadgeRuleCondition(field="availabilityStatus.quantity", operator=">", value=0)
            ],
            requiresAllConditions=True
        )
        
        result = badge_service._evaluate_conditions(sample_product, rule)
        assert result is True

    def test_evaluate_conditions_one_failed(self, badge_service, sample_product):
        """Test evaluating conditions when one fails."""
        rule = BadgeRule(
            badgeType=BadgeType.BEST_SELLER,
            name="Test",
            description="Test",
            conditions=[
                BadgeRuleCondition(field="salesMetrics.last30Days.units", operator=">=", value=5000),
                BadgeRuleCondition(field="availabilityStatus.quantity", operator=">", value=0)
            ],
            requiresAllConditions=True
        )
        
        result = badge_service._evaluate_conditions(sample_product, rule)
        assert result is False

    def test_evaluate_conditions_or_logic(self, badge_service, sample_product):
        """Test evaluating conditions with OR logic."""
        rule = BadgeRule(
            badgeType=BadgeType.TRENDING,
            name="Test",
            description="Test",
            conditions=[
                BadgeRuleCondition(field="salesMetrics.last30Days.units", operator=">=", value=5000),
                BadgeRuleCondition(field="viewMetrics.last7Days.views", operator=">=", value=500)
            ],
            requiresAllConditions=False
        )
        
        result = badge_service._evaluate_conditions(sample_product, rule)
        assert result is True


class TestEvaluateCondition:
    """Tests for _evaluate_condition method."""

    def test_evaluate_condition_greater_than_or_equal(self, badge_service):
        """Test >= operator."""
        product = {"price": 50}
        condition = BadgeRuleCondition(field="price", operator=">=", value=30)
        
        result = badge_service._evaluate_condition(product, condition)
        assert result is True

    def test_evaluate_condition_less_than_or_equal(self, badge_service):
        """Test <= operator."""
        product = {"stock": 5}
        condition = BadgeRuleCondition(field="stock", operator="<=", value=10)
        
        result = badge_service._evaluate_condition(product, condition)
        assert result is True

    def test_evaluate_condition_between(self, badge_service):
        """Test between operator."""
        product = {"price": 50}
        condition = BadgeRuleCondition(field="price", operator="between", value=[30, 100])
        
        result = badge_service._evaluate_condition(product, condition)
        assert result is True

    def test_evaluate_condition_field_not_found(self, badge_service):
        """Test condition with non-existent field."""
        product = {"price": 50}
        condition = BadgeRuleCondition(field="nonexistent", operator=">=", value=30)
        
        result = badge_service._evaluate_condition(product, condition)
        assert result is False


class TestGetNestedField:
    """Tests for _get_nested_field method."""

    def test_get_nested_field_simple(self, badge_service):
        """Test getting simple field."""
        obj = {"name": "Product"}
        result = badge_service._get_nested_field(obj, "name")
        assert result == "Product"

    def test_get_nested_field_nested(self, badge_service):
        """Test getting nested field."""
        obj = {"sales": {"last30Days": {"units": 1000}}}
        result = badge_service._get_nested_field(obj, "sales.last30Days.units")
        assert result == 1000

    def test_get_nested_field_not_found(self, badge_service):
        """Test getting non-existent field."""
        obj = {"name": "Product"}
        result = badge_service._get_nested_field(obj, "nonexistent")
        assert result is None


class TestRemoveExpiredBadges:
    """Tests for remove_expired_badges method."""

    @pytest.mark.asyncio
    async def test_remove_expired_badges(self, badge_service, mock_repository):
        """Test removing expired badges from products."""
        # Setup
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=30)
        
        products = [
            {
                "_id": "id1",
                "badges": [
                    {"type": "sale", "expiresAt": past},
                    {"type": "featured", "expiresAt": future}
                ]
            }
        ]
        mock_repository.find_many.return_value = products
        mock_repository.update.return_value = True
        
        # Execute
        result = await badge_service.remove_expired_badges()
        
        # Assert
        assert result["success"]
        assert result["badgesRemoved"] == 1
        assert result["productsUpdated"] == 1


class TestGetBadgeStatistics:
    """Tests for get_badge_statistics method."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, badge_service, mock_repository):
        """Test getting badge statistics."""
        # Setup
        products = [
            {
                "_id": "id1",
                "badges": [
                    {"type": "sale", "assignedBy": "admin"},
                    {"type": "featured", "assignedBy": None}
                ]
            },
            {
                "_id": "id2",
                "badges": [
                    {"type": "sale", "assignedBy": "admin"}
                ]
            }
        ]
        mock_repository.find_many.return_value = products
        
        # Execute
        stats = await badge_service.get_badge_statistics()
        
        # Assert
        assert stats.totalBadges == 3
        assert stats.badgesByType["sale"] == 2
        assert stats.badgesByType["featured"] == 1
        assert stats.productsWithBadges == 2
        assert stats.manualBadges == 2
        assert stats.automatedBadges == 1
