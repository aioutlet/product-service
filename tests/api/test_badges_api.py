"""
Unit tests for badge API endpoints.

Tests HTTP endpoints for badge management operations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from src.models.badge import BadgeType, Badge, BadgeStatistics
from src.api.badges import (
    assign_badge,
    remove_badge,
    bulk_assign_badge,
    get_product_badges,
    evaluate_badge_rules,
    remove_expired_badges,
    get_badge_statistics
)


@pytest.fixture
def mock_badge_service():
    """Create mock badge service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    return {"user_id": "admin-123", "sub": "admin-123", "role": "admin"}


class TestAssignBadgeEndpoint:
    """Tests for POST /badges/assign endpoint."""

    @pytest.mark.asyncio
    async def test_assign_badge_success(self, mock_badge_service, mock_current_user):
        """Test successfully assigning badge via API."""
        # Setup
        from src.models.badge import AssignBadgeRequest
        
        request = AssignBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.SALE,
            metadata={"discount": 20}
        )
        
        mock_badge_service.assign_badge.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "Test Product",
            "badges": [{"type": "sale"}]
        }
        
        # Execute
        result = await assign_badge(request, mock_current_user, mock_badge_service)
        
        # Assert
        assert result["success"] is True
        assert "Badge sale assigned" in result["message"]
        assert mock_badge_service.assign_badge.called

    @pytest.mark.asyncio
    async def test_assign_badge_product_not_found(self, mock_badge_service, mock_current_user):
        """Test assigning badge to non-existent product."""
        # Setup
        from src.models.badge import AssignBadgeRequest
        
        request = AssignBadgeRequest(
            productId="nonexistent",
            badgeType=BadgeType.SALE
        )
        
        mock_badge_service.assign_badge.side_effect = ValueError("Product nonexistent not found")
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await assign_badge(request, mock_current_user, mock_badge_service)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_assign_badge_already_exists(self, mock_badge_service, mock_current_user):
        """Test assigning badge that already exists."""
        # Setup
        from src.models.badge import AssignBadgeRequest
        
        request = AssignBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.SALE
        )
        
        mock_badge_service.assign_badge.side_effect = ValueError("Badge sale already assigned")
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await assign_badge(request, mock_current_user, mock_badge_service)
        
        assert exc_info.value.status_code == 400


class TestRemoveBadgeEndpoint:
    """Tests for POST /badges/remove endpoint."""

    @pytest.mark.asyncio
    async def test_remove_badge_success(self, mock_badge_service):
        """Test successfully removing badge via API."""
        # Setup
        from src.models.badge import RemoveBadgeRequest
        
        request = RemoveBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.SALE
        )
        
        mock_badge_service.remove_badge.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "badges": []
        }
        
        # Execute
        result = await remove_badge(request, mock_badge_service)
        
        # Assert
        assert result["success"] is True
        assert "Badge sale removed" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_badge_not_found(self, mock_badge_service):
        """Test removing badge that doesn't exist."""
        # Setup
        from src.models.badge import RemoveBadgeRequest
        
        request = RemoveBadgeRequest(
            productId="507f1f77bcf86cd799439011",
            badgeType=BadgeType.SALE
        )
        
        mock_badge_service.remove_badge.side_effect = ValueError("Badge sale not found")
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await remove_badge(request, mock_badge_service)
        
        assert exc_info.value.status_code == 400


class TestBulkAssignBadgeEndpoint:
    """Tests for POST /badges/bulk-assign endpoint."""

    @pytest.mark.asyncio
    async def test_bulk_assign_success(self, mock_badge_service, mock_current_user):
        """Test bulk assigning badges via API."""
        # Setup
        from src.models.badge import BulkAssignBadgeRequest
        
        request = BulkAssignBadgeRequest(
            productIds=["id1", "id2", "id3"],
            badgeType=BadgeType.SALE
        )
        
        mock_badge_service.bulk_assign_badge.return_value = {
            "totalProcessed": 3,
            "successCount": 3,
            "failedCount": 0,
            "skippedCount": 0
        }
        
        # Execute
        result = await bulk_assign_badge(request, mock_current_user, mock_badge_service)
        
        # Assert
        assert result["success"] is True
        assert result["data"]["successCount"] == 3


class TestGetProductBadgesEndpoint:
    """Tests for GET /badges/product/{product_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_product_badges_success(self, mock_badge_service):
        """Test getting product badges via API."""
        # Setup
        mock_badge_service.get_product_badges.return_value = {
            "productId": "507f1f77bcf86cd799439011",
            "badges": [
                {"type": "sale", "assignedAt": datetime.utcnow()}
            ],
            "displayBadge": {"type": "sale", "assignedAt": datetime.utcnow()}
        }
        
        # Execute
        result = await get_product_badges("507f1f77bcf86cd799439011", mock_badge_service)
        
        # Assert
        assert result["productId"] == "507f1f77bcf86cd799439011"
        assert len(result["badges"]) == 1

    @pytest.mark.asyncio
    async def test_get_product_badges_not_found(self, mock_badge_service):
        """Test getting badges for non-existent product."""
        # Setup
        mock_badge_service.get_product_badges.side_effect = ValueError("Product not found")
        
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_product_badges("nonexistent", mock_badge_service)
        
        assert exc_info.value.status_code == 404


class TestEvaluateBadgeRulesEndpoint:
    """Tests for POST /badges/evaluate-rules endpoint."""

    @pytest.mark.asyncio
    async def test_evaluate_rules_all_products(self, mock_badge_service):
        """Test evaluating rules for all products."""
        # Setup
        from src.models.badge import EvaluateBadgeRulesRequest
        
        request = EvaluateBadgeRulesRequest()
        
        mock_badge_service.evaluate_badge_rules.return_value = {
            "success": True,
            "productsEvaluated": 10,
            "results": [],
            "summary": {"badgesAdded": 5, "badgesRemoved": 2, "errors": 0}
        }
        
        # Execute
        result = await evaluate_badge_rules(request, mock_badge_service)
        
        # Assert
        assert result["success"] is True
        assert result["productsEvaluated"] == 10

    @pytest.mark.asyncio
    async def test_evaluate_rules_specific_products(self, mock_badge_service):
        """Test evaluating rules for specific products."""
        # Setup
        from src.models.badge import EvaluateBadgeRulesRequest
        
        request = EvaluateBadgeRulesRequest(
            productIds=["id1", "id2"],
            badgeTypes=[BadgeType.BEST_SELLER]
        )
        
        mock_badge_service.evaluate_badge_rules.return_value = {
            "success": True,
            "productsEvaluated": 2,
            "results": [],
            "summary": {"badgesAdded": 1, "badgesRemoved": 0, "errors": 0}
        }
        
        # Execute
        result = await evaluate_badge_rules(request, mock_badge_service)
        
        # Assert
        assert result["productsEvaluated"] == 2

    @pytest.mark.asyncio
    async def test_evaluate_rules_dry_run(self, mock_badge_service):
        """Test evaluating rules in dry run mode."""
        # Setup
        from src.models.badge import EvaluateBadgeRulesRequest
        
        request = EvaluateBadgeRulesRequest(dryRun=True)
        
        mock_badge_service.evaluate_badge_rules.return_value = {
            "success": True,
            "productsEvaluated": 5,
            "results": [],
            "summary": {"badgesAdded": 3, "badgesRemoved": 1, "errors": 0}
        }
        
        # Execute
        result = await evaluate_badge_rules(request, mock_badge_service)
        
        # Assert
        assert result["success"] is True


class TestRemoveExpiredBadgesEndpoint:
    """Tests for DELETE /badges/expired endpoint."""

    @pytest.mark.asyncio
    async def test_remove_expired_badges(self, mock_badge_service):
        """Test removing expired badges."""
        # Setup
        mock_badge_service.remove_expired_badges.return_value = {
            "success": True,
            "badgesRemoved": 5,
            "productsUpdated": 3
        }
        
        # Execute
        result = await remove_expired_badges(mock_badge_service)
        
        # Assert
        assert result["success"] is True
        assert result["data"]["badgesRemoved"] == 5


class TestGetBadgeStatisticsEndpoint:
    """Tests for GET /badges/statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_badge_service):
        """Test getting badge statistics."""
        # Setup
        mock_badge_service.get_badge_statistics.return_value = BadgeStatistics(
            totalBadges=150,
            badgesByType={"sale": 45, "best_seller": 30},
            productsWithBadges=120,
            automatedBadges=95,
            manualBadges=55,
            expiredBadges=5
        )
        
        # Execute
        result = await get_badge_statistics(mock_badge_service)
        
        # Assert
        assert result.totalBadges == 150
        assert result.badgesByType["sale"] == 45
        assert result.productsWithBadges == 120
