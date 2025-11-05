"""Unit tests for restrictions service."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.services.restrictions_service import RestrictionsService
from src.models.restrictions import (
    AgeRestriction,
    ShippingRestrictionType,
    ShippingRestriction,
    RegionalAvailability,
    ProductRestrictions
)
from src.models.product import ProductBase
from src.core.errors import ErrorResponse


@pytest.fixture
def mock_repository():
    """Create a mock product repository."""
    return AsyncMock()


@pytest.fixture
def restrictions_service(mock_repository):
    """Create restrictions service with mocked dependencies."""
    return RestrictionsService(repository=mock_repository)


@pytest.fixture
def sample_product():
    """Sample product for testing."""
    product = Mock()
    product._id = "prod123"
    product.name = "Test Product"
    product.sku = "TEST-SKU-001"
    product.price = 29.99
    product.description = "Test Description"
    product.category = "Test"
    product.created_by = "test_user"
    product.restrictions = None
    product.model_dump = Mock(return_value={
        "_id": "prod123",
        "name": "Test Product",
        "sku": "TEST-SKU-001",
        "price": 29.99,
        "description": "Test Description",
        "category": "Test",
        "created_by": "test_user",
        "restrictions": None
    })
    return product


@pytest.fixture
def sample_restrictions():
    """Sample restrictions for testing."""
    return ProductRestrictions(
        age_restriction=AgeRestriction.EIGHTEEN_PLUS,
        prescription_required=False,
        license_required=False
    )


class TestUpdateRestrictions:
    """Test update_restrictions method."""
    
    @pytest.mark.asyncio
    @patch('src.services.restrictions_service.get_dapr_publisher')
    async def test_update_success(
        self,
        mock_get_publisher,
        restrictions_service,
        mock_repository,
        sample_product,
        sample_restrictions
    ):
        """Test successful restrictions update."""
        # Setup
        mock_publisher = AsyncMock()
        mock_get_publisher.return_value = mock_publisher
        
        updated_product = Mock()
        updated_product._id = "prod123"
        updated_product.sku = "TEST-SKU-001"
        updated_product.restrictions = sample_restrictions
        updated_product.updated_at = datetime.now()
        updated_product.updated_by = "user123"
        
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = updated_product
        
        # Execute
        result = await restrictions_service.update_restrictions(
            product_id="prod123",
            restrictions=sample_restrictions,
            updated_by="user123",
            correlation_id="corr123"
        )
        
        # Verify
        assert result.product_id == "prod123"
        assert result.sku == "TEST-SKU-001"
        assert result.restrictions.age_restriction == AgeRestriction.EIGHTEEN_PLUS
        assert result.updated_by == "user123"
        
        mock_repository.find_by_id.assert_called_once_with("prod123", "corr123")
        mock_repository.update.assert_called_once()
        mock_publisher.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_product_not_found(
        self,
        restrictions_service,
        mock_repository,
        sample_restrictions
    ):
        """Test update fails when product not found."""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await restrictions_service.update_restrictions(
                product_id="nonexistent",
                restrictions=sample_restrictions
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    @patch('src.services.restrictions_service.get_dapr_publisher')
    async def test_update_repository_failure(
        self,
        mock_get_publisher,
        restrictions_service,
        mock_repository,
        sample_product,
        sample_restrictions
    ):
        """Test update handles repository failure."""
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await restrictions_service.update_restrictions(
                product_id="prod123",
                restrictions=sample_restrictions
            )
        
        assert exc_info.value.status_code == 500
        assert "failed to update" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    @patch('src.services.restrictions_service.get_dapr_publisher')
    async def test_update_with_full_restrictions(
        self,
        mock_get_publisher,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test update with complex restrictions."""
        mock_publisher = AsyncMock()
        mock_get_publisher.return_value = mock_publisher
        
        complex_restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.CUSTOM,
            custom_age_limit=16,
            shipping_restrictions=[
                ShippingRestriction(
                    type=ShippingRestrictionType.HAZMAT,
                    reason="Contains chemicals"
                )
            ],
            regional_availability=RegionalAvailability(
                available_countries=["US", "CA"]
            ),
            prescription_required=True,
            license_required=True
        )
        
        updated_product = Mock()
        updated_product._id = "prod123"
        updated_product.sku = "TEST-SKU-001"
        updated_product.restrictions = complex_restrictions
        
        mock_repository.find_by_id.return_value = sample_product
        mock_repository.update.return_value = updated_product
        
        result = await restrictions_service.update_restrictions(
            product_id="prod123",
            restrictions=complex_restrictions
        )
        
        assert result.restrictions.custom_age_limit == 16
        assert len(result.restrictions.shipping_restrictions) == 1
        assert result.restrictions.prescription_required is True


class TestGetRestrictions:
    """Test get_restrictions method."""
    
    @pytest.mark.asyncio
    async def test_get_success(
        self,
        restrictions_service,
        mock_repository,
        sample_product,
        sample_restrictions
    ):
        """Test successful retrieval of restrictions."""
        sample_product.restrictions = sample_restrictions
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.get_restrictions(
            product_id="prod123",
            correlation_id="corr123"
        )
        
        assert result.product_id == "prod123"
        assert result.restrictions.age_restriction == AgeRestriction.EIGHTEEN_PLUS
        mock_repository.find_by_id.assert_called_once_with("prod123", "corr123")
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(
        self,
        restrictions_service,
        mock_repository
    ):
        """Test get fails when product not found."""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(ErrorResponse) as exc_info:
            await restrictions_service.get_restrictions(product_id="nonexistent")
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_no_restrictions(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test get with product that has no restrictions."""
        sample_product.restrictions = None
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.get_restrictions(product_id="prod123")
        
        assert result.restrictions.age_restriction == AgeRestriction.NONE
        assert result.restrictions.prescription_required is False


class TestCheckAgeEligibility:
    """Test check_age_eligibility method."""
    
    @pytest.mark.asyncio
    async def test_no_restriction(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test age check with no restriction."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_age_eligibility(
            product_id="prod123",
            customer_age=15
        )
        
        assert result["eligible"] is True
        assert result["required_age"] is None
    
    @pytest.mark.asyncio
    async def test_18_plus_eligible(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test 18+ restriction with eligible customer."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.EIGHTEEN_PLUS,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_age_eligibility(
            product_id="prod123",
            customer_age=20
        )
        
        assert result["eligible"] is True
        assert result["required_age"] == 18
    
    @pytest.mark.asyncio
    async def test_18_plus_not_eligible(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test 18+ restriction with ineligible customer."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.EIGHTEEN_PLUS,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_age_eligibility(
            product_id="prod123",
            customer_age=17
        )
        
        assert result["eligible"] is False
        assert result["required_age"] == 18
    
    @pytest.mark.asyncio
    async def test_21_plus_eligible(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test 21+ restriction with eligible customer."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.TWENTY_ONE_PLUS,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_age_eligibility(
            product_id="prod123",
            customer_age=25
        )
        
        assert result["eligible"] is True
        assert result["required_age"] == 21
    
    @pytest.mark.asyncio
    async def test_custom_age_eligible(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test custom age restriction with eligible customer."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.CUSTOM,
            custom_age_limit=16,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_age_eligibility(
            product_id="prod123",
            customer_age=17
        )
        
        assert result["eligible"] is True
        assert result["required_age"] == 16


class TestCheckRegionalAvailability:
    """Test check_regional_availability method."""
    
    @pytest.mark.asyncio
    async def test_no_regional_restrictions(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test with no regional restrictions."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_regional_availability(
            product_id="prod123",
            country="US"
        )
        
        assert result["available"] is True
        assert result["reason"] is None
    
    @pytest.mark.asyncio
    async def test_available_country(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test country in available list."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            regional_availability=RegionalAvailability(
                available_countries=["US", "CA", "MX"]
            ),
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_regional_availability(
            product_id="prod123",
            country="US"
        )
        
        assert result["available"] is True
    
    @pytest.mark.asyncio
    async def test_restricted_country(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test country in restricted list."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            regional_availability=RegionalAvailability(
                restricted_countries=["IR", "KP"]
            ),
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_regional_availability(
            product_id="prod123",
            country="IR"
        )
        
        assert result["available"] is False
        assert "restricted" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_available_state(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test state in available list."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            regional_availability=RegionalAvailability(
                available_states={"US": ["CA", "NY", "TX"]}
            ),
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.check_regional_availability(
            product_id="prod123",
            country="US",
            state="CA"
        )
        
        assert result["available"] is True


class TestGetApplicableShippingRestrictions:
    """Test get_applicable_shipping_restrictions method."""
    
    @pytest.mark.asyncio
    async def test_no_shipping_restrictions(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test product with no shipping restrictions."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.get_applicable_shipping_restrictions(
            product_id="prod123"
        )
        
        assert result["product_id"] == "prod123"
        assert result["restrictions"] == []
    
    @pytest.mark.asyncio
    async def test_with_shipping_restrictions(
        self,
        restrictions_service,
        mock_repository,
        sample_product
    ):
        """Test product with shipping restrictions."""
        sample_product.restrictions = ProductRestrictions(
            age_restriction=AgeRestriction.NONE,
            shipping_restrictions=[
                ShippingRestriction(
                    type=ShippingRestrictionType.HAZMAT,
                    reason="Flammable liquid"
                ),
                ShippingRestriction(
                    type=ShippingRestrictionType.GROUND_ONLY,
                    reason="Cannot ship by air"
                )
            ],
            prescription_required=False,
            license_required=False
        )
        mock_repository.find_by_id.return_value = sample_product
        
        result = await restrictions_service.get_applicable_shipping_restrictions(
            product_id="prod123"
        )
        
        assert len(result["restrictions"]) == 2
        assert result["restrictions"][0]["type"] == ShippingRestrictionType.HAZMAT
        assert result["restrictions"][1]["type"] == ShippingRestrictionType.GROUND_ONLY
