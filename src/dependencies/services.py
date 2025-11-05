"""
Service layer dependency injection for FastAPI.

Provides service instances with proper dependencies injected.
"""

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from src.core.database import get_product_collection, get_db
from src.repositories.product_repository import ProductRepository
# Lazy imports to avoid circular dependencies - services import from dependencies.auth
# which imports from dependencies.__init__ which imports this file


async def get_size_charts_collection() -> AsyncIOMotorCollection:
    """
    FastAPI dependency to get size_charts collection.
    
    Returns:
        Size charts collection from database
    """
    db = await get_db()
    return db["size_charts"]


async def get_size_chart_repository(
    collection: AsyncIOMotorCollection = Depends(get_size_charts_collection)
):
    """
    FastAPI dependency to get SizeChartRepository instance.
    
    Usage:
        @router.get("/size-charts")
        async def list_size_charts(
            repo: SizeChartRepository = Depends(get_size_chart_repository)
        ):
            charts = await repo.list_all()
            ...
    
    Args:
        collection: Size charts collection from database dependency
        
    Returns:
        SizeChartRepository instance
    """
    from src.repositories.size_chart_repository import SizeChartRepository
    return SizeChartRepository(collection)


async def get_size_chart_service(
    repo = Depends(get_size_chart_repository)
):
    """
    FastAPI dependency to get SizeChartService instance.
    
    Usage:
        @router.post("/size-charts")
        async def create_size_chart(
            service: SizeChartService = Depends(get_size_chart_service)
        ):
            chart_id = await service.create_size_chart(...)
            ...
    
    Args:
        repo: Size chart repository from repository dependency
        
    Returns:
        SizeChartService instance
    """
    from src.services.size_chart_service import SizeChartService
    return SizeChartService(repo)


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
):
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
    from src.services.product_service import ProductService
    return ProductService(repo)


async def get_badge_service(
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    FastAPI dependency to get BadgeService instance.
    
    Usage:
        @router.post("/badges/assign")
        async def assign_badge(
            service: BadgeService = Depends(get_badge_service)
        ):
            result = await service.assign_badge(...)
            ...
    
    Args:
        repo: Product repository from repository dependency
        
    Returns:
        BadgeService instance
    """
    from src.services.badge_service import BadgeService
    return BadgeService(repo)


async def get_bulk_operations_service(
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    FastAPI dependency to get BulkOperationsService instance.
    
    Usage:
        @router.post("/products/bulk-create")
        async def bulk_create_products(
            service: BulkOperationsService = Depends(get_bulk_operations_service)
        ):
            result = await service.bulk_create(...)
            ...
    
    Args:
        repo: Product repository from repository dependency
        
    Returns:
        BulkOperationsService instance
    """
    from src.services.bulk_operations_service import BulkOperationsService
    return BulkOperationsService(repo)


async def get_import_export_service(
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    FastAPI dependency to get ImportExportService instance.
    
    Usage:
        @router.post("/products/import")
        async def import_products(
            service: ImportExportService = Depends(get_import_export_service)
        ):
            result = await service.import_products(...)
            ...
    
    Args:
        repo: Product repository from repository dependency
        
    Returns:
        ImportExportService instance
    """
    from src.services.import_export_service import ImportExportService
    return ImportExportService(repo)


async def get_restrictions_service(
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    FastAPI dependency to get RestrictionsService instance.
    
    Usage:
        @router.put("/restrictions/{product_id}")
        async def update_restrictions(
            product_id: str,
            service: RestrictionsService = Depends(get_restrictions_service)
        ):
            result = await service.update_restrictions(...)
            ...
    
    Args:
        repo: Product repository from repository dependency
        
    Returns:
        RestrictionsService instance
    """
    from src.services.restrictions_service import RestrictionsService
    return RestrictionsService(repo)
