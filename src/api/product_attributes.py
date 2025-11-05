"""
Product Attributes API

Endpoints for managing product attribute schemas and faceted search.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models.attribute_schema import (
    CategorySchema, CreateSchemaRequest, UpdateSchemaRequest,
    SchemaResponse, AttributeValidationResult, FacetedSearchResult
)
from src.models.product import ProductAttributes
from src.services.attribute_validation_service import AttributeValidationService
from src.services.faceted_search_service import FacetedSearchService
from src.repositories.attribute_schema_repository import AttributeSchemaRepository
from src.core.database import get_db
from src.dependencies.auth import require_admin
from src.core.logger import logger
from src.utils.correlation_id import get_correlation_id


router = APIRouter(prefix="/attributes", tags=["Product Attributes"])


def get_attribute_validation_service() -> AttributeValidationService:
    """Get attribute validation service instance"""
    return AttributeValidationService()


def get_schema_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AttributeSchemaRepository:
    """Get schema repository instance"""
    return AttributeSchemaRepository(db)


def get_faceted_search_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> FacetedSearchService:
    """Get faceted search service instance"""
    return FacetedSearchService(db)


@router.get("/schemas", response_model=List[SchemaResponse])
async def list_schemas(
    repository: AttributeSchemaRepository = Depends(get_schema_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    List all available attribute schemas.
    
    Returns all category schemas including standard schemas.
    """
    logger.info("Listing all attribute schemas", correlation_id=correlation_id)
    
    schemas = await repository.list_all(correlation_id=correlation_id)
    
    return [
        SchemaResponse(
            id=str(schema.get("_id")),
            category_name=schema["category_name"],
            display_name=schema["display_name"],
            attribute_groups=schema["attribute_groups"],
            version=schema.get("version", 1),
            is_active=schema.get("is_active", True),
            created_at=schema.get("created_at"),
            updated_at=schema.get("updated_at")
        )
        for schema in schemas
    ]


@router.get("/schemas/{category}", response_model=SchemaResponse)
async def get_schema(
    category: str,
    repository: AttributeSchemaRepository = Depends(get_schema_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get attribute schema for a specific category.
    
    Args:
        category: Product category name
        
    Returns:
        Category schema with attribute groups and definitions
    """
    logger.info(f"Getting schema for category: {category}", correlation_id=correlation_id)
    
    schema = await repository.get_by_category(category, correlation_id=correlation_id)
    
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema not found for category: {category}")
    
    return SchemaResponse(
        id=str(schema.get("_id")),
        category_name=schema["category_name"],
        display_name=schema["display_name"],
        attribute_groups=schema["attribute_groups"],
        version=schema.get("version", 1),
        is_active=schema.get("is_active", True),
        created_at=schema.get("created_at"),
        updated_at=schema.get("updated_at")
    )


@router.post("/schemas", response_model=Dict[str, str], dependencies=[Depends(require_admin)])
async def create_schema(
    request: CreateSchemaRequest,
    repository: AttributeSchemaRepository = Depends(get_schema_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Create a new attribute schema (Admin only).
    
    Args:
        request: Schema creation request
        
    Returns:
        Created schema ID
    """
    logger.info(f"Creating schema for category: {request.category_name}", correlation_id=correlation_id)
    
    # Check if schema already exists
    existing = await repository.get_by_category(request.category_name, correlation_id=correlation_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Schema already exists for category: {request.category_name}")
    
    # Create schema
    schema = CategorySchema(
        category_name=request.category_name,
        display_name=request.display_name,
        attribute_groups=request.attribute_groups,
        version=1,
        is_active=True
    )
    
    schema_id = await repository.create(schema, correlation_id=correlation_id)
    
    logger.info(f"Created schema {schema_id} for category {request.category_name}", correlation_id=correlation_id)
    
    return {"schema_id": schema_id, "category": request.category_name}


@router.put("/schemas/{category}", response_model=Dict[str, str], dependencies=[Depends(require_admin)])
async def update_schema(
    category: str,
    request: UpdateSchemaRequest,
    repository: AttributeSchemaRepository = Depends(get_schema_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Update an existing attribute schema (Admin only).
    
    Args:
        category: Category name
        request: Schema update request
        
    Returns:
        Success message
    """
    logger.info(f"Updating schema for category: {category}", correlation_id=correlation_id)
    
    # Check if schema exists
    existing = await repository.get_by_category(category, correlation_id=correlation_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schema not found for category: {category}")
    
    # Update schema
    updated_schema = CategorySchema(
        category_name=category,
        display_name=request.display_name or existing["display_name"],
        attribute_groups=request.attribute_groups or existing["attribute_groups"],
        version=existing.get("version", 1) + 1,
        is_active=request.is_active if request.is_active is not None else existing.get("is_active", True)
    )
    
    await repository.update(category, updated_schema, correlation_id=correlation_id)
    
    logger.info(f"Updated schema for category {category}", correlation_id=correlation_id)
    
    return {"message": "Schema updated successfully", "category": category}


@router.delete("/schemas/{category}", response_model=Dict[str, str], dependencies=[Depends(require_admin)])
async def delete_schema(
    category: str,
    repository: AttributeSchemaRepository = Depends(get_schema_repository),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Delete an attribute schema (Admin only).
    
    Args:
        category: Category name
        
    Returns:
        Success message
    """
    logger.info(f"Deleting schema for category: {category}", correlation_id=correlation_id)
    
    # Check if schema exists
    existing = await repository.get_by_category(category, correlation_id=correlation_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Schema not found for category: {category}")
    
    await repository.delete(category, correlation_id=correlation_id)
    
    logger.info(f"Deleted schema for category {category}", correlation_id=correlation_id)
    
    return {"message": "Schema deleted successfully", "category": category}


@router.post("/validate", response_model=AttributeValidationResult)
async def validate_attributes(
    category: str,
    attributes: ProductAttributes,
    validation_service: AttributeValidationService = Depends(get_attribute_validation_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Validate product attributes against category schema.
    
    Args:
        category: Product category
        attributes: Attributes to validate
        
    Returns:
        Validation result with errors and warnings
    """
    logger.info(f"Validating attributes for category: {category}", correlation_id=correlation_id)
    
    result = validation_service.validate_attributes(attributes, category)
    
    logger.info(
        f"Validation result: valid={result.is_valid}, errors={len(result.errors)}, warnings={len(result.warnings)}",
        correlation_id=correlation_id
    )
    
    return result


@router.get("/search/faceted", response_model=FacetedSearchResult)
async def faceted_search(
    category: Optional[str] = Query(None, description="Product category"),
    text_query: Optional[str] = Query(None, description="Text search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    faceted_search_service: FacetedSearchService = Depends(get_faceted_search_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Perform faceted search with attribute filtering.
    
    Query parameters:
    - category: Filter by category
    - text_query: Text search
    - page: Page number
    - page_size: Items per page
    - Any attribute path (e.g., attributes.category_specific.fit_type=Regular)
    
    Returns:
        Search results with facets and counts
    """
    # Get facet fields for category
    facet_fields = await faceted_search_service.get_available_facets(category, correlation_id=correlation_id)
    
    # Perform search
    result = await faceted_search_service.search_with_facets(
        text_query=text_query,
        category=category,
        facet_fields=facet_fields,
        page=page,
        page_size=page_size,
        correlation_id=correlation_id
    )
    
    return result


@router.get("/facets/{category}", response_model=List[str])
async def get_category_facets(
    category: str,
    faceted_search_service: FacetedSearchService = Depends(get_faceted_search_service),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get available facet fields for a category.
    
    Args:
        category: Product category
        
    Returns:
        List of attribute paths that can be used for faceting
    """
    logger.info(f"Getting facets for category: {category}", correlation_id=correlation_id)
    
    facet_fields = await faceted_search_service.get_available_facets(category, correlation_id=correlation_id)
    
    return facet_fields
