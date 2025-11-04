"""
Product Variation Service
Implements PRD REQ-8.1 to REQ-8.5: Product Variations Business Logic
"""
from typing import List, Dict, Any, Optional
from bson import ObjectId
from datetime import datetime, timezone

from src.db.mongodb import get_db
from src.models.variation_models import (
    ParentProductCreate,
    VariationCreate,
    VariationMatrix,
    ParentProductResponse,
    VariationUpdate
)
from src.observability import logger


class VariationService:
    """
    Service for managing product variations (REQ-8.1 to REQ-8.5)
    """
    
    def __init__(self, products_collection=None):
        self.products_collection = products_collection
    
    async def create_parent_with_variations(
        self,
        parent_data: ParentProductCreate,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Create parent product with all variations in single operation (REQ-8.5)
        
        Args:
            parent_data: Parent product and variations data
            created_by: User ID creating the product
            
        Returns:
            Created parent product with variation IDs
            
        Raises:
            ValueError: If validation fails (duplicate SKUs, etc.)
        """
        # Get collection if not provided
        if self.products_collection is None:
            db = await get_db()
            self.products_collection = db.products
        
        # Validate unique SKUs across all variations
        skus = [v.sku for v in parent_data.variations]
        if len(skus) != len(set(skus)):
            raise ValueError("Duplicate SKUs found in variations")
        
        # Check for existing SKUs in database
        existing_skus = await self.products_collection.count_documents({
            'sku': {'$in': skus}
        })
        if existing_skus > 0:
            raise ValueError(
                "One or more SKUs already exist in database"
            )
        
        # Validate variation attribute uniqueness (REQ-8.5)
        self._validate_variation_uniqueness(parent_data.variations)
        
        # Create parent product document
        now = datetime.now(timezone.utc)
        parent_doc = {
            '_id': ObjectId(),
            'name': parent_data.name,
            'description': parent_data.description,
            'brand': parent_data.brand,
            'department': parent_data.department,
            'category': parent_data.category,
            'subcategory': parent_data.subcategory,
            'variation_theme': parent_data.variation_theme.value,
            'base_price': parent_data.base_price,
            'images': parent_data.images or [],
            'tags': parent_data.tags or [],
            'specifications': parent_data.specifications or {},
            'is_parent': True,
            'variation_count': len(parent_data.variations),
            'is_active': True,
            'created_at': now,
            'updated_at': now,
            'created_by': created_by,
            'history': [{
                'action': 'created',
                'timestamp': now,
                'user_id': created_by
            }]
        }
        
        # Insert parent product
        await self.products_collection.insert_one(parent_doc)
        parent_id = str(parent_doc['_id'])
        
        logger.info(
            f"Created parent product: {parent_id}",
            metadata={
                'event': 'parent_product_created',
                'parentId': parent_id,
                'variationCount': len(parent_data.variations)
            }
        )
        
        # Create variation products (children)
        variation_ids = []
        for variation in parent_data.variations:
            variation_doc = self._build_variation_document(
                variation=variation,
                parent_id=parent_id,
                parent_data=parent_data,
                created_by=created_by,
                now=now
            )
            await self.products_collection.insert_one(variation_doc)
            variation_ids.append(str(variation_doc['_id']))
        
        logger.info(
            f"Created {len(variation_ids)} variations for parent {parent_id}",
            metadata={
                'event': 'variations_created',
                'parentId': parent_id,
                'variationIds': variation_ids
            }
        )
        
        return {
            'parent_id': parent_id,
            'variation_ids': variation_ids,
            'variation_count': len(variation_ids)
        }
    
    def _build_variation_document(
        self,
        variation: VariationCreate,
        parent_id: str,
        parent_data: ParentProductCreate,
        created_by: str,
        now: datetime
    ) -> Dict[str, Any]:
        """
        Build variation document with inheritance from parent (REQ-8.3)
        """
        # Build attribute dict for easier querying
        attributes_dict = {
            attr.name.lower(): attr.value
            for attr in variation.attributes
        }
        
        return {
            '_id': ObjectId(),
            'sku': variation.sku,
            'name': variation.name,
            'description': variation.description or parent_data.description,
            'price': variation.price,
            'brand': parent_data.brand,  # Inherited (REQ-8.3)
            'department': parent_data.department,  # Inherited
            'category': parent_data.category,  # Inherited
            'subcategory': parent_data.subcategory,  # Inherited
            'images': variation.images or [],
            'tags': list(set(
                (parent_data.tags or []) + (variation.tags or [])
            )),  # Merged
            'specifications': {
                **(parent_data.specifications or {}),
                **(variation.specifications or {})
            },  # Merged with override
            'parent_id': parent_id,
            'is_variation': True,
            'variation_attributes': [
                attr.model_dump() for attr in variation.attributes
            ],
            'variation_attributes_dict': attributes_dict,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
            'created_by': created_by,
            'history': [{
                'action': 'created',
                'timestamp': now,
                'user_id': created_by
            }]
        }
    
    def _validate_variation_uniqueness(
        self,
        variations: List[VariationCreate]
    ):
        """
        Validate no duplicate attribute combinations (REQ-8.5)
        For example, no two variations with color=Black AND size=M
        """
        attribute_combos = set()
        
        for variation in variations:
            # Create tuple of sorted attribute key-value pairs
            combo = tuple(sorted([
                (attr.name.lower(), attr.value.lower())
                for attr in variation.attributes
            ]))
            
            if combo in attribute_combos:
                raise ValueError(
                    "Duplicate variation attribute combination found"
                )
            attribute_combos.add(combo)
    
    async def get_parent_with_variations(
        self,
        parent_id: str
    ) -> Optional[ParentProductResponse]:
        """
        Get parent product with all variations (REQ-8.4)
        
        Args:
            parent_id: Parent product ID
            
        Returns:
            Parent product response with variation matrix
        """
        # Get collection if not provided
        if self.products_collection is None:
            db = await get_db()
            self.products_collection = db.products
        
        # Get parent product
        parent = await self.products_collection.find_one({
            '_id': ObjectId(parent_id),
            'is_parent': True,
            'is_active': True
        })
        
        if not parent:
            return None
        
        # Get all child variations
        variations_cursor = self.products_collection.find({
            'parent_id': parent_id,
            'is_variation': True,
            'is_active': True
        })
        variations = await variations_cursor.to_list(length=1000)
        
        # Build variation matrix (REQ-8.4)
        variation_matrix = []
        for variation in variations:
            attrs_dict = variation.get('variation_attributes_dict', {})
            variation_matrix.append(VariationMatrix(
                sku=variation['sku'],
                attributes=attrs_dict,
                price=variation['price'],
                available=variation.get('availability', {}).get(
                    'status'
                ) == 'in_stock',
                images=variation.get('images')
            ))
        
        return ParentProductResponse(
            parent_id=parent_id,
            name=parent['name'],
            description=parent['description'],
            brand=parent['brand'],
            department=parent.get('department'),
            category=parent.get('category'),
            subcategory=parent.get('subcategory'),
            variation_theme=parent['variation_theme'],
            images=parent.get('images'),
            tags=parent.get('tags'),
            specifications=parent.get('specifications'),
            variations=variation_matrix,
            total_variations=len(variation_matrix)
        )
    
    async def add_variation_to_parent(
        self,
        parent_id: str,
        variation: VariationCreate,
        created_by: str
    ) -> str:
        """
        Add new variation to existing parent (REQ-8.5)
        
        Args:
            parent_id: Parent product ID
            variation: Variation data
            created_by: User ID
            
        Returns:
            Created variation ID
        """
        # Get collection if not provided
        if self.products_collection is None:
            db = await get_db()
            self.products_collection = db.products
        
        # Get parent product
        parent = await self.products_collection.find_one({
            '_id': ObjectId(parent_id),
            'is_parent': True,
            'is_active': True
        })
        
        if not parent:
            raise ValueError(f"Parent product {parent_id} not found")
        
        # Check SKU uniqueness
        existing = await self.products_collection.count_documents({
            'sku': variation.sku
        })
        if existing > 0:
            raise ValueError(f"SKU {variation.sku} already exists")
        
        # Get existing variations to validate uniqueness
        existing_variations_cursor = self.products_collection.find({
            'parent_id': parent_id,
            'is_variation': True,
            'is_active': True
        })
        existing_variations = await existing_variations_cursor.to_list(
            length=1000
        )
        
        # Validate attribute combination uniqueness
        new_combo = tuple(sorted([
            (attr.name.lower(), attr.value.lower())
            for attr in variation.attributes
        ]))
        
        for existing_var in existing_variations:
            existing_attrs = existing_var.get('variation_attributes', [])
            existing_combo = tuple(sorted([
                (attr['name'].lower(), attr['value'].lower())
                for attr in existing_attrs
            ]))
            if new_combo == existing_combo:
                raise ValueError(
                    "Variation with same attributes already exists"
                )
        
        # Create variation document
        now = datetime.now(timezone.utc)
        parent_data_mock = ParentProductCreate(
            name=parent['name'],
            description=parent['description'],
            brand=parent['brand'],
            department=parent.get('department'),
            category=parent.get('category'),
            subcategory=parent.get('subcategory'),
            variation_theme=parent['variation_theme'],
            base_price=parent.get('base_price'),
            images=parent.get('images'),
            tags=parent.get('tags'),
            specifications=parent.get('specifications'),
            variations=[variation]  # Dummy for interface
        )
        
        variation_doc = self._build_variation_document(
            variation=variation,
            parent_id=parent_id,
            parent_data=parent_data_mock,
            created_by=created_by,
            now=now
        )
        
        await self.products_collection.insert_one(variation_doc)
        variation_id = str(variation_doc['_id'])
        
        # Update parent variation count
        await self.products_collection.update_one(
            {'_id': ObjectId(parent_id)},
            {
                '$inc': {'variation_count': 1},
                '$set': {'updated_at': now}
            }
        )
        
        logger.info(
            f"Added variation {variation_id} to parent {parent_id}",
            metadata={
                'event': 'variation_added',
                'parentId': parent_id,
                'variationId': variation_id
            }
        )
        
        return variation_id
    
    async def update_variation(
        self,
        variation_id: str,
        updates: VariationUpdate,
        updated_by: str
    ) -> bool:
        """
        Update variation attributes (REQ-8.5)
        
        Args:
            variation_id: Variation product ID
            updates: Update data
            updated_by: User ID
            
        Returns:
            True if updated successfully
        """
        # Get collection if not provided
        if self.products_collection is None:
            db = await get_db()
            self.products_collection = db.products
        
        # Build update document
        update_doc = {}
        if updates.name is not None:
            update_doc['name'] = updates.name
        if updates.price is not None:
            update_doc['price'] = updates.price
        if updates.images is not None:
            update_doc['images'] = updates.images
        if updates.description is not None:
            update_doc['description'] = updates.description
        if updates.specifications is not None:
            update_doc['specifications'] = updates.specifications
        if updates.tags is not None:
            update_doc['tags'] = updates.tags
        if updates.is_active is not None:
            update_doc['is_active'] = updates.is_active
        
        if updates.attributes is not None:
            update_doc['variation_attributes'] = [
                attr.model_dump() for attr in updates.attributes
            ]
            update_doc['variation_attributes_dict'] = {
                attr.name.lower(): attr.value
                for attr in updates.attributes
            }
        
        if not update_doc:
            return False
        
        now = datetime.now(timezone.utc)
        update_doc['updated_at'] = now
        
        result = await self.products_collection.update_one(
            {
                '_id': ObjectId(variation_id),
                'is_variation': True
            },
            {
                '$set': update_doc,
                '$push': {
                    'history': {
                        'action': 'updated',
                        'timestamp': now,
                        'user_id': updated_by,
                        'changes': list(update_doc.keys())
                    }
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(
                f"Updated variation {variation_id}",
                metadata={
                    'event': 'variation_updated',
                    'variationId': variation_id,
                    'updatedFields': list(update_doc.keys())
                }
            )
            return True
        
        return False
    
    async def delete_variation(
        self,
        variation_id: str,
        deleted_by: str
    ) -> bool:
        """
        Soft delete variation (REQ-8.5)
        
        Args:
            variation_id: Variation product ID
            deleted_by: User ID
            
        Returns:
            True if deleted successfully
        """
        # Get collection if not provided
        if self.products_collection is None:
            db = await get_db()
            self.products_collection = db.products
        
        now = datetime.now(timezone.utc)
        
        # Get variation to find parent
        variation = await self.products_collection.find_one({
            '_id': ObjectId(variation_id),
            'is_variation': True
        })
        
        if not variation:
            return False
        
        parent_id = variation.get('parent_id')
        
        # Soft delete variation
        result = await self.products_collection.update_one(
            {'_id': ObjectId(variation_id)},
            {
                '$set': {
                    'is_active': False,
                    'updated_at': now
                },
                '$push': {
                    'history': {
                        'action': 'deleted',
                        'timestamp': now,
                        'user_id': deleted_by
                    }
                }
            }
        )
        
        if result.modified_count > 0 and parent_id:
            # Update parent variation count
            await self.products_collection.update_one(
                {'_id': ObjectId(parent_id)},
                {
                    '$inc': {'variation_count': -1},
                    '$set': {'updated_at': now}
                }
            )
            
            logger.info(
                f"Deleted variation {variation_id}",
                metadata={
                    'event': 'variation_deleted',
                    'variationId': variation_id,
                    'parentId': parent_id
                }
            )
            return True
        
        return False
    
    async def filter_variations(
        self,
        parent_id: str,
        attribute_filters: Dict[str, str]
    ) -> List[VariationMatrix]:
        """
        Filter variations by attribute values (REQ-8.4)
        
        Args:
            parent_id: Parent product ID
            attribute_filters: Attribute filters (e.g., {'color': 'Black'})
            
        Returns:
            Filtered variation matrix
        """
        # Get collection if not provided
        if self.products_collection is None:
            db = await get_db()
            self.products_collection = db.products
        
        # Build MongoDB query for attribute filtering
        query = {
            'parent_id': parent_id,
            'is_variation': True,
            'is_active': True
        }
        
        # Add attribute filters to query
        for attr_name, attr_value in attribute_filters.items():
            query[f'variation_attributes_dict.{attr_name.lower()}'] = (
                attr_value
            )
        
        variations_cursor = self.products_collection.find(query)
        variations = await variations_cursor.to_list(length=1000)
        
        # Build variation matrix
        variation_matrix = []
        for variation in variations:
            attrs_dict = variation.get('variation_attributes_dict', {})
            variation_matrix.append(VariationMatrix(
                sku=variation['sku'],
                attributes=attrs_dict,
                price=variation['price'],
                available=variation.get('availability', {}).get(
                    'status'
                ) == 'in_stock',
                images=variation.get('images')
            ))
        
        return variation_matrix


# Singleton instance
_variation_service = None


def get_variation_service() -> VariationService:
    """Get singleton variation service instance"""
    global _variation_service
    if _variation_service is None:
        _variation_service = VariationService()
    return _variation_service
