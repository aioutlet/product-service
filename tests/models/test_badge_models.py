"""
Unit tests for badge models.

Tests validation, serialization, and business rules for badge data models.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models.badge import (
    BadgeType,
    BadgePriority,
    Badge,
    BadgeRuleCondition,
    BadgeRule,
    AssignBadgeRequest,
    RemoveBadgeRequest,
    BulkAssignBadgeRequest,
    EvaluateBadgeRulesRequest,
    BadgeEvaluationResult,
    BadgeRuleEvaluationResponse,
    ProductBadgesResponse,
    BadgeStatistics
)


class TestBadgeType:
    """Tests for BadgeType enum."""

    def test_badge_type_values(self):
        """Test all badge type values are defined."""
        assert BadgeType.NEW.value == "new"
        assert BadgeType.SALE.value == "sale"
        assert BadgeType.TRENDING.value == "trending"
        assert BadgeType.FEATURED.value == "featured"
        assert BadgeType.BEST_SELLER.value == "best_seller"
        assert BadgeType.LOW_STOCK.value == "low_stock"

    def test_badge_type_from_string(self):
        """Test creating BadgeType from string."""
        assert BadgeType("new") == BadgeType.NEW
        assert BadgeType("sale") == BadgeType.SALE


class TestBadgePriority:
    """Tests for BadgePriority enum."""

    def test_priority_values(self):
        """Test badge priority values are correctly ordered."""
        assert BadgePriority.FEATURED.value > BadgePriority.BEST_SELLER.value
        assert BadgePriority.BEST_SELLER.value > BadgePriority.TRENDING.value
        assert BadgePriority.TRENDING.value > BadgePriority.SALE.value
        assert BadgePriority.SALE.value > BadgePriority.LOW_STOCK.value
        assert BadgePriority.LOW_STOCK.value > BadgePriority.NEW.value


class TestBadge:
    """Tests for Badge model."""

    def test_create_badge_minimal(self):
        """Test creating badge with minimal required fields."""
        badge = Badge(type=BadgeType.SALE)
        
        assert badge.type == BadgeType.SALE
        assert badge.assignedBy is None
        assert badge.expiresAt is None
        assert badge.metadata == {}
        assert isinstance(badge.assignedAt, datetime)

    def test_create_badge_complete(self):
        """Test creating badge with all fields."""
        now = datetime.utcnow()
        expires = now + timedelta(days=30)
        
        badge = Badge(
            type=BadgeType.FEATURED,
            assignedBy="admin-123",
            expiresAt=expires,
            metadata={"campaign": "holiday-sale"}
        )
        
        assert badge.type == BadgeType.FEATURED
        assert badge.assignedBy == "admin-123"
        assert badge.expiresAt == expires
        assert badge.metadata == {"campaign": "holiday-sale"}

    def test_badge_serialization(self):
        """Test badge serialization to dict."""
        badge = Badge(
            type=BadgeType.SALE,
            assignedBy="user-456",
            metadata={"discount": 20}
        )
        
        data = badge.model_dump()
        assert data["type"] == "sale"
        assert data["assignedBy"] == "user-456"
        assert data["metadata"]["discount"] == 20


class TestBadgeRuleCondition:
    """Tests for BadgeRuleCondition model."""

    def test_create_condition_valid_operator(self):
        """Test creating condition with valid operator."""
        condition = BadgeRuleCondition(
            field="salesMetrics.last30Days.units",
            operator=">=",
            value=1000
        )
        
        assert condition.field == "salesMetrics.last30Days.units"
        assert condition.operator == ">="
        assert condition.value == 1000

    def test_create_condition_invalid_operator(self):
        """Test creating condition with invalid operator fails."""
        with pytest.raises(ValidationError) as exc_info:
            BadgeRuleCondition(
                field="price",
                operator="contains",
                value=50
            )
        
        assert "Operator must be one of" in str(exc_info.value)

    def test_all_valid_operators(self):
        """Test all valid operators are accepted."""
        operators = [">=", "<=", "==", ">", "<", "!=", "between", "in", "not_in"]
        
        for op in operators:
            condition = BadgeRuleCondition(
                field="test",
                operator=op,
                value=100
            )
            assert condition.operator == op


class TestBadgeRule:
    """Tests for BadgeRule model."""

    def test_create_rule_single_condition(self):
        """Test creating badge rule with single condition."""
        rule = BadgeRule(
            badgeType=BadgeType.BEST_SELLER,
            name="Best Seller Rule",
            description="Products with high sales",
            conditions=[
                BadgeRuleCondition(field="sales", operator=">=", value=1000)
            ]
        )
        
        assert rule.badgeType == BadgeType.BEST_SELLER
        assert rule.name == "Best Seller Rule"
        assert len(rule.conditions) == 1
        assert rule.requiresAllConditions is True
        assert rule.isActive is True

    def test_create_rule_multiple_conditions(self):
        """Test creating badge rule with multiple conditions."""
        rule = BadgeRule(
            badgeType=BadgeType.TRENDING,
            name="Trending Rule",
            description="High views and sales",
            conditions=[
                BadgeRuleCondition(field="views", operator=">=", value=500),
                BadgeRuleCondition(field="sales", operator=">=", value=50)
            ],
            requiresAllConditions=True
        )
        
        assert len(rule.conditions) == 2
        assert rule.requiresAllConditions is True

    def test_rule_requires_at_least_one_condition(self):
        """Test rule validation fails without conditions."""
        with pytest.raises(ValidationError):
            BadgeRule(
                badgeType=BadgeType.NEW,
                name="Invalid Rule",
                description="No conditions",
                conditions=[]
            )


class TestAssignBadgeRequest:
    """Tests for AssignBadgeRequest model."""

    def test_create_request_minimal(self):
        """Test creating request with minimal fields."""
        request = AssignBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.SALE
        )
        
        assert request.productId == "507f1f77bcf86cd799439011"
        assert request.badgeType == BadgeType.SALE
        assert request.expiresAt is None
        assert request.metadata == {}

    def test_create_request_complete(self):
        """Test creating request with all fields."""
        expires = datetime.utcnow() + timedelta(days=30)
        request = AssignBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.FEATURED,
            expiresAt=expires,
            metadata={"priority": "high"}
        )
        
        assert request.expiresAt == expires
        assert request.metadata == {"priority": "high"}


class TestRemoveBadgeRequest:
    """Tests for RemoveBadgeRequest model."""

    def test_create_remove_request(self):
        """Test creating remove badge request."""
        request = RemoveBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.SALE
        )
        
        assert request.productId == "507f1f77bcf86cd799439011"
        assert request.badgeType == BadgeType.SALE


class TestBulkAssignBadgeRequest:
    """Tests for BulkAssignBadgeRequest model."""

    def test_create_bulk_request(self):
        """Test creating bulk assignment request."""
        request = BulkAssignBadgeRequest(
            productIds=["id1", "id2", "id3"],
            badgeType=BadgeType.SALE,
            metadata={"discount": 25}
        )
        
        assert len(request.productIds) == 3
        assert request.badgeType == BadgeType.SALE
        assert request.metadata["discount"] == 25

    def test_bulk_request_requires_products(self):
        """Test bulk request validation fails without products."""
        with pytest.raises(ValidationError):
            BulkAssignBadgeRequest(
                productIds=[],
                badgeType=BadgeType.SALE
            )


class TestEvaluateBadgeRulesRequest:
    """Tests for EvaluateBadgeRulesRequest model."""

    def test_create_evaluate_request_all_products(self):
        """Test creating evaluation request for all products."""
        request = EvaluateBadgeRulesRequest()
        
        assert request.productIds is None
        assert request.badgeTypes is None
        assert request.dryRun is False

    def test_create_evaluate_request_specific_products(self):
        """Test creating evaluation request for specific products."""
        request = EvaluateBadgeRulesRequest(
            productIds=["id1", "id2"],
            badgeTypes=[BadgeType.BEST_SELLER, BadgeType.TRENDING],
            dryRun=True
        )
        
        assert request.productIds == ["id1", "id2"]
        assert len(request.badgeTypes) == 2
        assert request.dryRun is True


class TestBadgeEvaluationResult:
    """Tests for BadgeEvaluationResult model."""

    def test_create_result_no_changes(self):
        """Test creating result with no badge changes."""
        result = BadgeEvaluationResult(productId="id1")
        
        assert result.productId == "id1"
        assert result.badgesAdded == []
        assert result.badgesRemoved == []
        assert result.errors == []

    def test_create_result_with_changes(self):
        """Test creating result with badge changes."""
        result = BadgeEvaluationResult(
            productId="id1",
            badgesAdded=[BadgeType.BEST_SELLER, BadgeType.TRENDING],
            badgesRemoved=[BadgeType.NEW],
            errors=[]
        )
        
        assert len(result.badgesAdded) == 2
        assert len(result.badgesRemoved) == 1
        assert result.errors == []

    def test_create_result_with_errors(self):
        """Test creating result with errors."""
        result = BadgeEvaluationResult(
            productId="id1",
            errors=["Failed to update product", "Database error"]
        )
        
        assert len(result.errors) == 2


class TestBadgeRuleEvaluationResponse:
    """Tests for BadgeRuleEvaluationResponse model."""

    def test_create_response(self):
        """Test creating evaluation response."""
        response = BadgeRuleEvaluationResponse(
            success=True,
            productsEvaluated=10,
            results=[
                BadgeEvaluationResult(
                    productId="id1",
                    badgesAdded=[BadgeType.BEST_SELLER]
                )
            ],
            summary={"badgesAdded": 5, "badgesRemoved": 2}
        )
        
        assert response.success is True
        assert response.productsEvaluated == 10
        assert len(response.results) == 1
        assert response.summary["badgesAdded"] == 5


class TestProductBadgesResponse:
    """Tests for ProductBadgesResponse model."""

    def test_create_response_no_badges(self):
        """Test creating response with no badges."""
        response = ProductBadgesResponse(
            productId="id1",
            badges=[]
        )
        
        assert response.productId == "id1"
        assert response.badges == []
        assert response.displayBadge is None

    def test_create_response_with_badges(self):
        """Test creating response with badges."""
        badge1 = Badge(type=BadgeType.SALE)
        badge2 = Badge(type=BadgeType.BEST_SELLER)
        
        response = ProductBadgesResponse(
            productId="id1",
            badges=[badge1, badge2],
            displayBadge=badge2
        )
        
        assert len(response.badges) == 2
        assert response.displayBadge.type == BadgeType.BEST_SELLER


class TestBadgeStatistics:
    """Tests for BadgeStatistics model."""

    def test_create_statistics(self):
        """Test creating badge statistics."""
        stats = BadgeStatistics(
            totalBadges=150,
            badgesByType={
                "sale": 45,
                "best_seller": 30,
                "trending": 25
            },
            productsWithBadges=120,
            automatedBadges=95,
            manualBadges=55,
            expiredBadges=5
        )
        
        assert stats.totalBadges == 150
        assert stats.badgesByType["sale"] == 45
        assert stats.productsWithBadges == 120
        assert stats.automatedBadges == 95
        assert stats.manualBadges == 55
        assert stats.expiredBadges == 5
