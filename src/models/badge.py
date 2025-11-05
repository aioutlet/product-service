"""
Badge models for product badge management.

This module defines data models for badge types, badge assignment rules,
automated badge evaluation, and badge-related API requests/responses.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class BadgeType(str, Enum):
    """Enumeration of available badge types."""
    NEW = "new"
    SALE = "sale"
    TRENDING = "trending"
    FEATURED = "featured"
    BEST_SELLER = "best_seller"
    LOW_STOCK = "low_stock"


class BadgePriority(int, Enum):
    """Badge display priority (higher number = higher priority)."""
    NEW = 1
    LOW_STOCK = 2
    SALE = 3
    TRENDING = 4
    BEST_SELLER = 5
    FEATURED = 6


class Badge(BaseModel):
    """Individual badge assigned to a product."""
    type: BadgeType
    assignedAt: datetime = Field(default_factory=datetime.utcnow)
    assignedBy: Optional[str] = None  # User ID who assigned (None for automated)
    expiresAt: Optional[datetime] = None  # Optional expiration date
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional badge-specific data

    class Config:
        json_schema_extra = {
            "example": {
                "type": "sale",
                "assignedAt": "2025-11-05T10:00:00Z",
                "assignedBy": "admin-user-123",
                "expiresAt": "2025-11-30T23:59:59Z",
                "metadata": {"discount_percentage": 20}
            }
        }


class BadgeRuleCondition(BaseModel):
    """Condition for automated badge assignment."""
    field: str  # e.g., "salesMetrics.last30Days.units", "availabilityStatus.quantity"
    operator: str  # e.g., ">=", "<=", "==", ">", "<", "between"
    value: Any  # Threshold value(s)

    @field_validator('operator')
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate operator is one of the allowed values."""
        allowed = [">=", "<=", "==", ">", "<", "!=", "between", "in", "not_in"]
        if v not in allowed:
            raise ValueError(f"Operator must be one of {allowed}")
        return v


class BadgeRule(BaseModel):
    """Automated badge assignment rule."""
    badgeType: BadgeType
    name: str
    description: str
    conditions: List[BadgeRuleCondition] = Field(min_length=1)
    requiresAllConditions: bool = True  # AND vs OR logic
    isActive: bool = True
    priority: int = 0
    autoRemoveWhenInvalid: bool = True  # Remove badge if conditions no longer met

    class Config:
        json_schema_extra = {
            "example": {
                "badgeType": "best_seller",
                "name": "Best Seller Rule",
                "description": "Assign best seller badge to products with 1000+ sales in last 30 days",
                "conditions": [
                    {
                        "field": "salesMetrics.last30Days.units",
                        "operator": ">=",
                        "value": 1000
                    }
                ],
                "requiresAllConditions": True,
                "isActive": True,
                "priority": 10,
                "autoRemoveWhenInvalid": True
            }
        }


class AssignBadgeRequest(BaseModel):
    """Request to manually assign a badge to a product."""
    productId: str
    badgeType: BadgeType
    expiresAt: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "productId": "507f1f77bcf86cd799439011",
                "badgeType": "featured",
                "expiresAt": "2025-12-31T23:59:59Z",
                "metadata": {"campaign": "holiday-sale"}
            }
        }


class RemoveBadgeRequest(BaseModel):
    """Request to remove a badge from a product."""
    productId: str
    badgeType: BadgeType

    class Config:
        json_schema_extra = {
            "example": {
                "productId": "507f1f77bcf86cd799439011",
                "badgeType": "sale"
            }
        }


class BulkAssignBadgeRequest(BaseModel):
    """Request to assign a badge to multiple products."""
    productIds: List[str] = Field(min_length=1)
    badgeType: BadgeType
    expiresAt: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "productIds": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"],
                "badgeType": "sale",
                "expiresAt": "2025-11-30T23:59:59Z",
                "metadata": {"discount_percentage": 25}
            }
        }


class EvaluateBadgeRulesRequest(BaseModel):
    """Request to evaluate badge rules for product(s)."""
    productIds: Optional[List[str]] = None  # None = evaluate all active products
    badgeTypes: Optional[List[BadgeType]] = None  # None = evaluate all badge types
    dryRun: bool = False  # If True, return what would change without applying

    class Config:
        json_schema_extra = {
            "example": {
                "productIds": ["507f1f77bcf86cd799439011"],
                "badgeTypes": ["best_seller", "trending"],
                "dryRun": False
            }
        }


class BadgeEvaluationResult(BaseModel):
    """Result of badge rule evaluation for a product."""
    productId: str
    badgesAdded: List[BadgeType] = Field(default_factory=list)
    badgesRemoved: List[BadgeType] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class BadgeRuleEvaluationResponse(BaseModel):
    """Response from badge rule evaluation."""
    success: bool
    productsEvaluated: int
    results: List[BadgeEvaluationResult]
    summary: Dict[str, int]  # e.g., {"badgesAdded": 5, "badgesRemoved": 2}

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "productsEvaluated": 10,
                "results": [
                    {
                        "productId": "507f1f77bcf86cd799439011",
                        "badgesAdded": ["best_seller"],
                        "badgesRemoved": [],
                        "errors": []
                    }
                ],
                "summary": {
                    "badgesAdded": 5,
                    "badgesRemoved": 2,
                    "errors": 0
                }
            }
        }


class ProductBadgesResponse(BaseModel):
    """Response containing product's current badges."""
    productId: str
    badges: List[Badge]
    displayBadge: Optional[Badge] = None  # Highest priority badge to display

    class Config:
        json_schema_extra = {
            "example": {
                "productId": "507f1f77bcf86cd799439011",
                "badges": [
                    {
                        "type": "sale",
                        "assignedAt": "2025-11-05T10:00:00Z",
                        "assignedBy": "admin-123",
                        "expiresAt": "2025-11-30T23:59:59Z",
                        "metadata": {"discount_percentage": 20}
                    },
                    {
                        "type": "best_seller",
                        "assignedAt": "2025-11-01T00:00:00Z",
                        "assignedBy": None,
                        "expiresAt": None,
                        "metadata": {"salesLast30Days": 1500}
                    }
                ],
                "displayBadge": {
                    "type": "best_seller",
                    "assignedAt": "2025-11-01T00:00:00Z",
                    "assignedBy": None,
                    "expiresAt": None,
                    "metadata": {"salesLast30Days": 1500}
                }
            }
        }


class BadgeStatistics(BaseModel):
    """Statistics about badge usage across the platform."""
    totalBadges: int
    badgesByType: Dict[str, int]
    productsWithBadges: int
    automatedBadges: int
    manualBadges: int
    expiredBadges: int

    class Config:
        json_schema_extra = {
            "example": {
                "totalBadges": 150,
                "badgesByType": {
                    "sale": 45,
                    "best_seller": 30,
                    "trending": 25,
                    "featured": 20,
                    "new": 20,
                    "low_stock": 10
                },
                "productsWithBadges": 120,
                "automatedBadges": 95,
                "manualBadges": 55,
                "expiredBadges": 5
            }
        }
