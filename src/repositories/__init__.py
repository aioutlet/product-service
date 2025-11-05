"""
Repository layer for data access.

This module contains repository classes that handle database operations
using the Repository pattern to abstract data access logic.
"""

from src.repositories.base_repository import BaseRepository
from src.repositories.product_repository import ProductRepository

__all__ = ["BaseRepository", "ProductRepository"]
