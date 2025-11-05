"""
Service layer dependency injection for FastAPI.

Provides service instances with proper dependencies injected.
"""

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from src.core.database import get_product_collection
from src.repositories.product_repository import ProductRepository
from src.services.product_service import ProductService


async def get_product_repository(
    collection: AsyncIOMotorCollection = Depends(get_product_collection)
) -> ProductRepository:
    """
    FastAPI dependency to get ProductRepository instance.
    
    Usage:
        @router.get("/products")
        async def list_products(
            repo: ProductRepository = Depends(get_product_repository)
        ):
            products, total = await repo.get_active_products()
            ...
    
    Args:
        collection: Products collection from database dependency
        
    Returns:
        ProductRepository instance
    """
    return ProductRepository(collection)


async def get_product_service(
    repo: ProductRepository = Depends(get_product_repository)
) -> ProductService:
    """
    FastAPI dependency to get ProductService instance.
    
    Usage:
        @router.get("/products")
        async def list_products(
            service: ProductService = Depends(get_product_service)
        ):
            products, total = await service.get_active_products()
            ...
    
    Args:
        repo: Product repository from repository dependency
        
    Returns:
        ProductService instance
    """
    return ProductService(repo)
