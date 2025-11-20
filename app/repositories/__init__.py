"""
Repositories module initialization
"""

from .product import ProductRepository
from .processed_events import ProcessedEventRepository

__all__ = [
    "ProductRepository",
    "ProcessedEventRepository",
]