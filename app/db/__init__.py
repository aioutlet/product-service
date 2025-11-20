"""
Database module initialization
"""

from .mongodb import db, connect_to_mongo, close_mongo_connection, get_product_collection

__all__ = [
    "db",
    "connect_to_mongo",
    "close_mongo_connection",
    "get_product_collection",
]