"""
Faceted Search Service

Provides faceted search with attribute-based filtering and aggregations.
"""

from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models.attribute_schema import Facet, FacetValue, FacetedSearchResult
from src.core.logger import logger


class FacetedSearchService:
    """
    Service for faceted search with attribute filtering.
    
    Provides:
    - Attribute-based filtering
    - Facet aggregation with counts
    - Multi-select filtering
    - Combined text + attribute search
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with database connection"""
        self.db = db
        self.collection = db.products
    
    async def search_with_facets(
        self,
        text_query: Optional[str] = None,
        category: Optional[str] = None,
        attribute_filters: Optional[Dict[str, List[str]]] = None,
        facet_fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20,
        correlation_id: Optional[str] = None
    ) -> FacetedSearchResult:
        """
        Perform faceted search with attribute filtering and sorting.
        
        Args:
            text_query: Optional text search query
            category: Optional category filter
            attribute_filters: Dict of attribute paths to filter values
                Example: {
                    "attributes.category_specific.fit_type": ["Regular", "Slim"],
                    "attributes.materials_composition.primary_material": ["Cotton"]
                }
            facet_fields: List of attribute paths to generate facets for
            sort_by: Field to sort by (supports attribute paths like "structured_attributes.physical_dimensions.weight")
            sort_order: Sort order, either "asc" or "desc" (default: "asc")
            page: Page number (1-indexed)
            page_size: Items per page
            correlation_id: For logging
            
        Returns:
            FacetedSearchResult with products and facets
        """
        logger.info(
            f"Faceted search: query={text_query}, category={category}, filters={attribute_filters}, sort={sort_by}",
            correlation_id=correlation_id
        )
        
        # Build base query
        query = {"is_active": True}
        
        # Add text search
        if text_query:
            query["$text"] = {"$search": text_query}
        
        # Add category filter
        if category:
            query["category"] = category
        
        # Add attribute filters
        if attribute_filters:
            for attr_path, values in attribute_filters.items():
                if values:
                    query[attr_path] = {"$in": values}
        
        # Count total matches
        total_count = await self.collection.count_documents(query)
        
        # Build sort criteria
        sort_criteria = []
        if sort_by:
            # Validate sort order
            if sort_order.lower() not in ["asc", "desc"]:
                sort_order = "asc"
            
            sort_direction = 1 if sort_order.lower() == "asc" else -1
            sort_criteria.append((sort_by, sort_direction))
        
        # Always add _id as secondary sort for consistency
        sort_criteria.append(("_id", 1))
        
        # Fetch products (paginated with sorting)
        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort(sort_criteria).skip(skip).limit(page_size)
        products = await cursor.to_list(length=page_size)
        
        # Generate facets
        facets = []
        if facet_fields:
            for field in facet_fields:
                facet = await self._generate_facet(field, query, attribute_filters, correlation_id)
                if facet:
                    facets.append(facet)
        
        logger.info(
            f"Found {total_count} products, {len(facets)} facets",
            correlation_id=correlation_id
        )
        
        return FacetedSearchResult(
            products=products,
            facets=facets,
            total_count=total_count,
            applied_filters=attribute_filters or {},
            page=page,
            page_size=page_size
        )
    
    async def _generate_facet(
        self,
        field: str,
        base_query: Dict[str, Any],
        current_filters: Optional[Dict[str, List[str]]],
        correlation_id: Optional[str] = None
    ) -> Optional[Facet]:
        """
        Generate a single facet with value counts.
        
        Args:
            field: Attribute field path (e.g., "attributes.category_specific.fit_type")
            base_query: Base query without this field's filter
            current_filters: Currently applied filters
            correlation_id: For logging
            
        Returns:
            Facet with values and counts
        """
        # Remove this field's filter from query to show all available values
        facet_query = {k: v for k, v in base_query.items() if k != field}
        
        # Aggregate to get value counts
        pipeline = [
            {"$match": facet_query},
            {"$group": {
                "_id": f"${field}",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 50}  # Limit to top 50 values
        ]
        
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=50)
        
        if not results:
            return None
        
        # Build facet values
        values = []
        for result in results:
            value = result["_id"]
            count = result["count"]
            
            # Skip null values
            if value is None:
                continue
            
            # Handle list values (take first item)
            if isinstance(value, list):
                if not value:
                    continue
                value = value[0]
            
            values.append(FacetValue(
                value=str(value),
                count=count,
                display_name=str(value)
            ))
        
        if not values:
            return None
        
        # Get display name from field path
        display_name = field.split('.')[-1].replace('_', ' ').title()
        
        # Get selected values
        selected_values = []
        if current_filters and field in current_filters:
            selected_values = current_filters[field]
        
        return Facet(
            attribute_name=field,
            display_name=display_name,
            values=values,
            selected_values=selected_values
        )
    
    async def get_available_facets(
        self,
        category: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Get list of available facet fields for a category.
        
        Args:
            category: Product category
            correlation_id: For logging
            
        Returns:
            List of attribute field paths that can be used for faceting
        """
        # Common facet fields
        facet_fields = [
            "category",
            "brand",
            "attributes.category_specific.fit_type",
            "attributes.category_specific.neckline",
            "attributes.category_specific.sleeve_length",
            "attributes.category_specific.pattern",
            "attributes.category_specific.occasion",
            "attributes.category_specific.season",
            "attributes.category_specific.gender",
            "attributes.category_specific.room_type",
            "attributes.category_specific.style",
            "attributes.category_specific.skin_type",
            "attributes.materials_composition.primary_material",
            "attributes.sustainability.eco_friendly",
            "attributes.care_instructions.washing",
            "attributes.care_instructions.drying"
        ]
        
        # Category-specific facets
        if category == "Clothing":
            return [f for f in facet_fields if any(x in f for x in ["fit_type", "neckline", "sleeve", "pattern", "occasion", "season", "gender", "material"])]
        elif category == "Electronics":
            return ["brand", "category", "attributes.category_specific.operating_system", "attributes.technical_specs.warranty_duration_months"]
        elif category == "Home & Furniture":
            return [f for f in facet_fields if any(x in f for x in ["room_type", "style", "material", "assembly"])]
        elif category == "Beauty & Personal Care":
            return [f for f in facet_fields if any(x in f for x in ["skin_type", "fragrance", "cruelty", "vegan"])]
        else:
            return ["category", "brand"]
    
    async def search_by_attributes(
        self,
        category: str,
        attributes: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search products by specific attribute values.
        
        Args:
            category: Product category
            attributes: Attribute filters (flat dict)
            page: Page number
            page_size: Items per page
            correlation_id: For logging
            
        Returns:
            Dict with products and pagination info
        """
        query = {
            "is_active": True,
            "category": category
        }
        
        # Add attribute filters
        for key, value in attributes.items():
            if value is not None:
                # Handle nested attributes
                if '.' not in key:
                    key = f"attributes.{key}"
                query[key] = value
        
        # Count and fetch
        total_count = await self.collection.count_documents(query)
        skip = (page - 1) * page_size
        
        cursor = self.collection.find(query).skip(skip).limit(page_size)
        products = await cursor.to_list(length=page_size)
        
        return {
            "products": products,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
