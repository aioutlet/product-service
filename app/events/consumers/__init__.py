"""
Event consumers
"""

from .review_consumer import review_event_consumer, ReviewEventConsumer
from .inventory_consumer import inventory_event_consumer, InventoryEventConsumer

__all__ = [
    "review_event_consumer",
    "ReviewEventConsumer",
    "inventory_event_consumer",
    "InventoryEventConsumer"
]
