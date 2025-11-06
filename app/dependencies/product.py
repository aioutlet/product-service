"""
Dependency injection for Product service and repository
"""

from fastapi import Depends

from app.db.mongodb import get_product_collection
from app.repositories.product import ProductRepository
from app.services.product import ProductService


async def get_product_repository() -> ProductRepository:
    """Get product repository instance"""
    collection = await get_product_collection()
    return ProductRepository(collection)


async def get_product_service(
    repository: ProductRepository = Depends(get_product_repository)
) -> ProductService:
    """Get product service instance"""
    return ProductService(repository)