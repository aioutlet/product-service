"""
Product Variation Service

Handles parent-child product relationships and variant attribute management.
Supports independent and shared inventory modes.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from bson import ObjectId

from src.models.variation import (
    VariationType,
    InventoryMode,
    CreateVariationRequest,
    UpdateVariationRequest,
    VariationRelationship,
    ProductVariationSummary,
    VariantAttribute,
    VariantAttributeMatrix,
    VariationConfiguration,
    BulkCreateVariationsRequest,
    BulkCreateVariationsResponse,
    VariationValidationError
)
from src.services.dapr_publisher import get_dapr_publisher
from src.core.logger import logger
from src.core.errors import ErrorResponse
from src.repositories.product_repository import ProductRepository


class VariationService:
    """Service for managing product variations."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def create_variation(
        self,
        request: CreateVariationRequest,
        acting_user: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Create a child variation product.
        
        Args:
            request: Variation creation request
            acting_user: User creating the variation
            correlation_id: Correlation ID for logging
            
        Returns:
            Created variation product ID
            
        Raises:
            ErrorResponse: If parent doesn't exist, SKU exists, or validation fails
        """
        logger.info(
            f"Creating variation for parent {request.parent_id}",
            correlation_id=correlation_id,
            metadata={
                "parent_id": request.parent_id,
                "sku": request.sku,
                "attributes": [f"{a.name}={a.value}" for a in request.variant_attributes]
            }
        )
        
        try:
            # Validate parent exists and is a parent product
            parent = await self.repository.find_by_id(request.parent_id, correlation_id)
            if not parent:
                raise ErrorResponse(
                    f"Parent product {request.parent_id} not found",
                    status_code=404
                )
            
            if parent.get("variation_type") != VariationType.PARENT:
                raise ErrorResponse(
                    "Parent product must have variation_type='parent'",
                    status_code=400
                )
            
            # Check SKU uniqueness
            is_unique = await self.repository.is_sku_unique(request.sku, correlation_id)
            if not is_unique:
                raise ErrorResponse(
                    f"SKU {request.sku} already exists",
                    status_code=409
                )
            
            # Validate variant attributes match parent's configuration
            await self._validate_variant_attributes(
                parent,
                request.variant_attributes,
                correlation_id
            )
            
            # Build child product data
            child_data = {
                "name": request.name,
                "sku": request.sku,
                "variation_type": VariationType.CHILD,
                "parent_id": request.parent_id,
                "variant_attributes": [attr.dict() for attr in request.variant_attributes],
                "is_active": request.is_active,
                "created_by": acting_user,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                
                # Inherit from parent or override
                "price": request.price or parent.get("price"),
                "compare_at_price": request.compare_at_price or parent.get("compare_at_price"),
                "description": request.description or parent.get("description"),
                "long_description": parent.get("long_description"),
                "brand": parent.get("brand"),
                "status": parent.get("status", "active"),
                
                # Inherit taxonomy
                "department": parent.get("department"),
                "category": parent.get("category"),
                "subcategory": parent.get("subcategory"),
                "product_type": parent.get("product_type"),
                
                # Images (use variant images or inherit from parent)
                "images": request.images or parent.get("images", []),
                
                # Inherit attributes but don't override variant_attributes
                "attributes": parent.get("attributes", {}),
                "specifications": parent.get("specifications", {}),
                "tags": parent.get("tags", []),
                "search_keywords": parent.get("search_keywords", []),
                "seo": parent.get("seo"),
                "restrictions": parent.get("restrictions"),
            }
            
            # Create child product
            child_id = await self.repository.create(child_data, correlation_id)
            
            # Update parent's child_skus and child_count
            await self._update_parent_children(request.parent_id, correlation_id)
            
            logger.info(
                f"Variation created: {child_id}",
                correlation_id=correlation_id,
                metadata={
                    "child_id": child_id,
                    "parent_id": request.parent_id,
                    "sku": request.sku
                }
            )
            
            # Publish variation.created event
            try:
                publisher = get_dapr_publisher()
                await publisher.publish_variation_created(
                    parent_id=request.parent_id,
                    variation_id=child_id,
                    variation_type=parent.get("variation_config", {}).get("type", "unknown"),
                    variant_attributes={attr.name: attr.value for attr in request.variant_attributes},
                    created_by=acting_user,
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.error(
                    f"Failed to publish variation.created event: {str(e)}",
                    metadata={"parent_id": request.parent_id, "variation_id": child_id}
                )
            
            return child_id
            
        except ErrorResponse:
            raise
        except Exception as e:
            logger.error(
                "Error creating variation",
                correlation_id=correlation_id,
                error=e,
                metadata={"parent_id": request.parent_id}
            )
            raise
    
    async def update_variation(
        self,
        variation_id: str,
        request: UpdateVariationRequest,
        acting_user: str,
        correlation_id: Optional[str] = None
    ) -> Dict:
        """
        Update a child variation product.
        
        Args:
            variation_id: Variation product ID
            request: Update request
            acting_user: User updating the variation
            correlation_id: Correlation ID for logging
            
        Returns:
            Updated variation data
            
        Raises:
            ErrorResponse: If variation doesn't exist or validation fails
        """
        logger.info(
            f"Updating variation {variation_id}",
            correlation_id=correlation_id,
            metadata={"variation_id": variation_id}
        )
        
        try:
            # Get existing variation
            variation = await self.repository.find_by_id(variation_id, correlation_id)
            if not variation:
                raise ErrorResponse(
                    f"Variation {variation_id} not found",
                    status_code=404
                )
            
            if variation.get("variation_type") != VariationType.CHILD:
                raise ErrorResponse(
                    "Product is not a variation",
                    status_code=400
                )
            
            # Build update data
            update_data = {}
            
            if request.name is not None:
                update_data["name"] = request.name
            if request.price is not None:
                update_data["price"] = request.price
            if request.compare_at_price is not None:
                update_data["compare_at_price"] = request.compare_at_price
            if request.description is not None:
                update_data["description"] = request.description
            if request.images is not None:
                update_data["images"] = request.images
            if request.is_active is not None:
                update_data["is_active"] = request.is_active
            
            # Validate and update variant attributes if provided
            if request.variant_attributes:
                parent = await self.repository.find_by_id(
                    variation.get("parent_id"),
                    correlation_id
                )
                if parent:
                    await self._validate_variant_attributes(
                        parent,
                        request.variant_attributes,
                        correlation_id
                    )
                update_data["variant_attributes"] = [
                    attr.dict() for attr in request.variant_attributes
                ]
            
            if not update_data:
                raise ErrorResponse("No fields to update", status_code=400)
            
            update_data["updated_by"] = acting_user
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update variation
            updated = await self.repository.update(
                variation_id,
                update_data,
                correlation_id
            )
            
            # Update parent's child list if activation status changed
            if request.is_active is not None:
                await self._update_parent_children(
                    variation.get("parent_id"),
                    correlation_id
                )
            
            logger.info(
                f"Variation updated: {variation_id}",
                correlation_id=correlation_id,
                metadata={"variation_id": variation_id}
            )
            
            # Publish variation.updated event
            try:
                publisher = get_dapr_publisher()
                await publisher.publish_variation_updated(
                    parent_id=variation.get("parent_id"),
                    variation_id=variation_id,
                    changes=update_data,
                    updated_by=acting_user,
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.error(
                    f"Failed to publish variation.updated event: {str(e)}",
                    metadata={"variation_id": variation_id}
                )
            
            return updated
            
        except ErrorResponse:
            raise
        except Exception as e:
            logger.error(
                "Error updating variation",
                correlation_id=correlation_id,
                error=e,
                metadata={"variation_id": variation_id}
            )
            raise
    
    async def get_variation_relationship(
        self,
        product_id: str,
        correlation_id: Optional[str] = None
    ) -> VariationRelationship:
        """
        Get complete variation relationship for a product.
        
        If product is a parent, returns parent + all children.
        If product is a child, returns its parent + all siblings.
        
        Args:
            product_id: Product ID (parent or child)
            correlation_id: Correlation ID for logging
            
        Returns:
            Complete variation relationship
            
        Raises:
            ErrorResponse: If product doesn't exist
        """
        logger.info(
            f"Getting variation relationship for {product_id}",
            correlation_id=correlation_id
        )
        
        try:
            product = await self.repository.find_by_id(product_id, correlation_id)
            if not product:
                raise ErrorResponse(
                    f"Product {product_id} not found",
                    status_code=404
                )
            
            variation_type = product.get("variation_type", VariationType.STANDALONE)
            
            if variation_type == VariationType.PARENT:
                parent = product
                parent_id = str(product["_id"])
            elif variation_type == VariationType.CHILD:
                parent_id = product.get("parent_id")
                parent = await self.repository.find_by_id(parent_id, correlation_id)
                if not parent:
                    raise ErrorResponse(
                        f"Parent product {parent_id} not found",
                        status_code=404
                    )
            else:
                # Standalone product - no variations
                return VariationRelationship(
                    parent=self._build_variation_summary(product),
                    children=[]
                )
            
            # Get all children
            children = await self.repository.find_many(
                {"parent_id": parent_id, "is_active": True},
                correlation_id=correlation_id
            )
            
            # Build relationship
            relationship = VariationRelationship(
                parent=self._build_variation_summary(parent),
                children=[self._build_variation_summary(child) for child in children],
                attribute_matrix=await self._build_attribute_matrix(
                    parent,
                    children,
                    correlation_id
                )
            )
            
            return relationship
            
        except ErrorResponse:
            raise
        except Exception as e:
            logger.error(
                "Error getting variation relationship",
                correlation_id=correlation_id,
                error=e,
                metadata={"product_id": product_id}
            )
            raise
    
    async def bulk_create_variations(
        self,
        request: BulkCreateVariationsRequest,
        acting_user: str,
        correlation_id: Optional[str] = None
    ) -> BulkCreateVariationsResponse:
        """
        Create multiple variations in bulk.
        
        Args:
            request: Bulk creation request
            acting_user: User creating variations
            correlation_id: Correlation ID for logging
            
        Returns:
            Bulk creation response with success/failure details
        """
        logger.info(
            f"Bulk creating {len(request.variations)} variations",
            correlation_id=correlation_id,
            metadata={"parent_id": request.parent_id, "count": len(request.variations)}
        )
        
        response = BulkCreateVariationsResponse(
            success_count=0,
            failure_count=0
        )
        
        for idx, variation in enumerate(request.variations):
            try:
                # Auto-generate name if requested
                if request.auto_generate_names:
                    parent = await self.repository.find_by_id(
                        request.parent_id,
                        correlation_id
                    )
                    if parent:
                        attr_str = ", ".join([
                            f"{a.value}" for a in variation.variant_attributes
                        ])
                        variation.name = f"{parent.get('name')} - {attr_str}"
                
                child_id = await self.create_variation(
                    variation,
                    acting_user,
                    correlation_id
                )
                response.created_ids.append(child_id)
                response.success_count += 1
                
            except ErrorResponse as e:
                response.failure_count += 1
                response.errors.append(VariationValidationError(
                    field="variation",
                    message=str(e),
                    variation_index=idx
                ))
            except Exception as e:
                response.failure_count += 1
                response.errors.append(VariationValidationError(
                    field="variation",
                    message=f"Unexpected error: {str(e)}",
                    variation_index=idx
                ))
        
        logger.info(
            f"Bulk creation complete: {response.success_count} success, {response.failure_count} failed",
            correlation_id=correlation_id,
            metadata={
                "parent_id": request.parent_id,
                "success": response.success_count,
                "failed": response.failure_count
            }
        )
        
        return response
    
    # ===== Private Helper Methods =====
    
    async def _validate_variant_attributes(
        self,
        parent: Dict,
        attributes: List[VariantAttribute],
        correlation_id: Optional[str] = None
    ):
        """Validate variant attributes against parent's configuration."""
        # TODO: Implement validation against parent's variant_attribute_definitions
        # For now, just basic validation
        if not attributes:
            raise ErrorResponse(
                "At least one variant attribute is required",
                status_code=400
            )
        
        # Check for duplicate attribute names
        attr_names = [a.name for a in attributes]
        if len(attr_names) != len(set(attr_names)):
            raise ErrorResponse(
                "Duplicate variant attribute names not allowed",
                status_code=400
            )
    
    async def _update_parent_children(
        self,
        parent_id: str,
        correlation_id: Optional[str] = None
    ):
        """Update parent's child_skus and child_count."""
        children = await self.repository.find_many(
            {"parent_id": parent_id, "is_active": True},
            correlation_id=correlation_id
        )
        
        child_skus = [child.get("sku") for child in children if child.get("sku")]
        child_count = len(children)
        
        await self.repository.update(
            parent_id,
            {
                "child_skus": child_skus,
                "child_count": child_count,
                "updated_at": datetime.now(timezone.utc)
            },
            correlation_id
        )
    
    def _build_variation_summary(self, product: Dict) -> ProductVariationSummary:
        """Build variation summary from product data."""
        return ProductVariationSummary(
            product_id=str(product["_id"]),
            product_name=product.get("name", ""),
            variation_type=product.get("variation_type", VariationType.STANDALONE),
            parent_id=product.get("parent_id"),
            child_count=product.get("child_count", 0),
            available_child_count=product.get("child_count", 0),  # TODO: Count only active
            variant_attributes=[
                VariantAttribute(**attr) 
                for attr in product.get("variant_attributes", [])
            ],
            price_range={
                "min": product.get("price", 0),
                "max": product.get("price", 0)
            } if product.get("price") else None
        )
    
    async def _build_attribute_matrix(
        self,
        parent: Dict,
        children: List[Dict],
        correlation_id: Optional[str] = None
    ) -> VariantAttributeMatrix:
        """Build attribute matrix showing all combinations."""
        if not children:
            return VariantAttributeMatrix(attribute_names=[], combinations=[])
        
        # Extract unique attribute names from children
        attr_names_set = set()
        for child in children:
            for attr in child.get("variant_attributes", []):
                attr_names_set.add(attr.get("name"))
        
        attr_names = sorted(list(attr_names_set))
        
        # Build combinations
        combinations = []
        for child in children:
            attrs_dict = {
                attr.get("name"): attr.get("value")
                for attr in child.get("variant_attributes", [])
            }
            combinations.append({
                "product_id": str(child["_id"]),
                "sku": child.get("sku"),
                "attributes": attrs_dict,
                "price": child.get("price"),
                "is_available": child.get("is_active", True),
                "stock_quantity": child.get("stock_quantity", 0)
            })
        
        return VariantAttributeMatrix(
            attribute_names=attr_names,
            combinations=combinations
        )
