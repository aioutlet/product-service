"""
Unit tests for faceted search service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.faceted_search_service import FacetedSearchService
from src.models.attribute_schema import FacetedSearchResult, Facet, FacetValue


@pytest.fixture
def mock_db():
    """Create mock database"""
    db = MagicMock()
    db.products = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create faceted search service"""
    return FacetedSearchService(mock_db)


class TestServiceInitialization:
    """Test service initialization"""
    
    def test_service_creation(self, mock_db):
        """Test creating service instance"""
        service = FacetedSearchService(mock_db)
        assert service is not None
        assert service.db == mock_db
        assert service.collection == mock_db.products


class TestSearchWithFacets:
    """Test faceted search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_without_filters(self, service, mock_db):
        """Test search without any filters"""
        # Mock count_documents
        mock_db.products.count_documents = AsyncMock(return_value=50)
        
        # Mock find with cursor
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[
            {"id": "1", "name": "Product 1"},
            {"id": "2", "name": "Product 2"}
        ])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            page=1,
            page_size=20
        )
        
        assert isinstance(result, FacetedSearchResult)
        assert result.total_count == 50
        assert len(result.products) == 2
        assert result.page == 1
    
    @pytest.mark.asyncio
    async def test_search_with_text_query(self, service, mock_db):
        """Test search with text query"""
        mock_db.products.count_documents = AsyncMock(return_value=10)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            text_query="shirt",
            page=1,
            page_size=20
        )
        
        # Verify text search was added to query
        call_args = mock_db.products.find.call_args[0][0]
        assert "$text" in call_args
        assert call_args["$text"]["$search"] == "shirt"
    
    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, service, mock_db):
        """Test search with category filter"""
        mock_db.products.count_documents = AsyncMock(return_value=25)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            category="Clothing",
            page=1,
            page_size=20
        )
        
        # Verify category was added to query
        call_args = mock_db.products.find.call_args[0][0]
        assert call_args["category"] == "Clothing"
    
    @pytest.mark.asyncio
    async def test_search_with_attribute_filters(self, service, mock_db):
        """Test search with attribute filters"""
        mock_db.products.count_documents = AsyncMock(return_value=15)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        attribute_filters = {
            "attributes.category_specific.fit_type": ["Regular", "Slim"]
        }
        
        result = await service.search_with_facets(
            attribute_filters=attribute_filters,
            page=1,
            page_size=20
        )
        
        # Verify attribute filters were added
        call_args = mock_db.products.find.call_args[0][0]
        assert "attributes.category_specific.fit_type" in call_args
        assert call_args["attributes.category_specific.fit_type"]["$in"] == ["Regular", "Slim"]
    
    @pytest.mark.asyncio
    async def test_search_pagination(self, service, mock_db):
        """Test search pagination"""
        mock_db.products.count_documents = AsyncMock(return_value=100)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            page=3,
            page_size=20
        )
        
        # Verify pagination
        mock_cursor.skip.assert_called_once_with(40)  # (3-1) * 20
        mock_cursor.limit.assert_called_once_with(20)
        assert result.page == 3
        assert result.page_size == 20


class TestGenerateFacet:
    """Test facet generation"""
    
    @pytest.mark.asyncio
    async def test_generate_facet_with_values(self, service, mock_db):
        """Test generating facet with values"""
        # Mock aggregate
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "Regular", "count": 25},
            {"_id": "Slim", "count": 15}
        ])
        mock_db.products.aggregate.return_value = mock_cursor
        
        base_query = {"is_active": True}
        facet = await service._generate_facet(
            "attributes.category_specific.fit_type",
            base_query,
            None
        )
        
        assert facet is not None
        assert facet.attribute_name == "attributes.category_specific.fit_type"
        assert len(facet.values) == 2
        assert facet.values[0].value == "Regular"
        assert facet.values[0].count == 25
    
    @pytest.mark.asyncio
    async def test_generate_facet_no_results(self, service, mock_db):
        """Test generating facet with no results"""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.aggregate.return_value = mock_cursor
        
        facet = await service._generate_facet(
            "attributes.category_specific.fit_type",
            {"is_active": True},
            None
        )
        
        assert facet is None
    
    @pytest.mark.asyncio
    async def test_generate_facet_with_selected_values(self, service, mock_db):
        """Test generating facet with selected values"""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "Regular", "count": 25}
        ])
        mock_db.products.aggregate.return_value = mock_cursor
        
        current_filters = {
            "attributes.category_specific.fit_type": ["Regular"]
        }
        
        facet = await service._generate_facet(
            "attributes.category_specific.fit_type",
            {"is_active": True},
            current_filters
        )
        
        assert facet is not None
        assert facet.selected_values == ["Regular"]
    
    @pytest.mark.asyncio
    async def test_generate_facet_skips_null_values(self, service, mock_db):
        """Test facet generation skips null values"""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": None, "count": 10},
            {"_id": "Regular", "count": 25}
        ])
        mock_db.products.aggregate.return_value = mock_cursor
        
        facet = await service._generate_facet(
            "attributes.category_specific.fit_type",
            {"is_active": True},
            None
        )
        
        assert facet is not None
        assert len(facet.values) == 1
        assert facet.values[0].value == "Regular"
    
    @pytest.mark.asyncio
    async def test_generate_facet_handles_list_values(self, service, mock_db):
        """Test facet generation handles list values"""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": ["Cotton", "Polyester"], "count": 5},
            {"_id": "Regular", "count": 25}
        ])
        mock_db.products.aggregate.return_value = mock_cursor
        
        facet = await service._generate_facet(
            "attributes.category_specific.fit_type",
            {"is_active": True},
            None
        )
        
        assert facet is not None
        # Should use first item from list
        assert len(facet.values) == 2


class TestGetAvailableFacets:
    """Test getting available facet fields"""
    
    @pytest.mark.asyncio
    async def test_get_facets_for_clothing(self, service):
        """Test getting facets for clothing category"""
        facets = await service.get_available_facets("Clothing")
        
        assert isinstance(facets, list)
        assert len(facets) > 0
        assert any("fit_type" in f for f in facets)
        assert any("material" in f for f in facets)
    
    @pytest.mark.asyncio
    async def test_get_facets_for_electronics(self, service):
        """Test getting facets for electronics category"""
        facets = await service.get_available_facets("Electronics")
        
        assert isinstance(facets, list)
        assert any("brand" in f for f in facets)
    
    @pytest.mark.asyncio
    async def test_get_facets_no_category(self, service):
        """Test getting facets without category"""
        facets = await service.get_available_facets(None)
        
        assert isinstance(facets, list)
        # Should return generic facets
        assert "category" in facets
        assert "brand" in facets


class TestSearchByAttributes:
    """Test search by specific attributes"""
    
    @pytest.mark.asyncio
    async def test_search_by_single_attribute(self, service, mock_db):
        """Test searching by single attribute"""
        mock_db.products.count_documents = AsyncMock(return_value=10)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[
            {"id": "1", "name": "Product 1"}
        ])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_by_attributes(
            category="Clothing",
            attributes={"fit_type": "Regular"},
            page=1,
            page_size=20
        )
        
        assert result["total"] == 10
        assert len(result["products"]) == 1
        assert result["page"] == 1
    
    @pytest.mark.asyncio
    async def test_search_by_multiple_attributes(self, service, mock_db):
        """Test searching by multiple attributes"""
        mock_db.products.count_documents = AsyncMock(return_value=5)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_by_attributes(
            category="Clothing",
            attributes={
                "fit_type": "Regular",
                "neckline": "Crew Neck"
            },
            page=1,
            page_size=20
        )
        
        assert result["total"] == 5
        
        # Verify both attributes in query
        call_args = mock_db.products.find.call_args[0][0]
        assert "attributes.fit_type" in call_args
        assert "attributes.neckline" in call_args
    
    @pytest.mark.asyncio
    async def test_search_ignores_none_values(self, service, mock_db):
        """Test search ignores None attribute values"""
        mock_db.products.count_documents = AsyncMock(return_value=10)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_by_attributes(
            category="Clothing",
            attributes={
                "fit_type": "Regular",
                "neckline": None
            },
            page=1,
            page_size=20
        )
        
        # Verify only non-None attributes in query
        call_args = mock_db.products.find.call_args[0][0]
        assert "attributes.fit_type" in call_args
        assert "attributes.neckline" not in call_args
    
    @pytest.mark.asyncio
    async def test_search_pagination_calculation(self, service, mock_db):
        """Test pagination calculation"""
        mock_db.products.count_documents = AsyncMock(return_value=47)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_by_attributes(
            category="Clothing",
            attributes={"fit_type": "Regular"},
            page=1,
            page_size=20
        )
        
        assert result["total"] == 47
        assert result["total_pages"] == 3  # ceil(47/20) = 3


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_search_empty_results(self, service, mock_db):
        """Test search with no results"""
        mock_db.products.count_documents = AsyncMock(return_value=0)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            category="Clothing",
            page=1,
            page_size=20
        )
        
        assert result.total_count == 0
        assert len(result.products) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_correlation_id(self, service, mock_db):
        """Test search with correlation ID for logging"""
        mock_db.products.count_documents = AsyncMock(return_value=10)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            category="Clothing",
            page=1,
            page_size=20,
            correlation_id="test-123"
        )
        
        # Should complete without error
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_with_empty_attribute_filters(self, service, mock_db):
        """Test search with empty attribute filters dict"""
        mock_db.products.count_documents = AsyncMock(return_value=10)
        
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.find.return_value = mock_cursor
        
        result = await service.search_with_facets(
            attribute_filters={},
            page=1,
            page_size=20
        )
        
        assert result is not None
        # Empty filters shouldn't add any filter clauses
        call_args = mock_db.products.find.call_args[0][0]
        assert "is_active" in call_args
