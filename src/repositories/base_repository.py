"""
Base repository pattern for MongoDB data access.

Provides generic CRUD operations for MongoDB collections with async/await support.
All domain-specific repositories should inherit from BaseRepository.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from src.core.logger import logger

# Generic type for Pydantic models
T = TypeVar("T", bound=BaseModel)


class BaseRepository:
    """
    Base repository providing generic CRUD operations for MongoDB collections.
    
    Usage:
        class ProductRepository(BaseRepository[ProductDB]):
            def __init__(self, collection: AsyncIOMotorCollection):
                super().__init__(collection, ProductDB)
    """
    
    def __init__(self, collection: AsyncIOMotorCollection, model_class: Type[T]):
        """
        Initialize repository.
        
        Args:
            collection: MongoDB collection instance
            model_class: Pydantic model class for type validation
        """
        self.collection = collection
        self.model_class = model_class
        self.collection_name = collection.name
    
    async def create(self, document: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        """
        Create a new document.
        
        Args:
            document: Document data to insert
            correlation_id: Optional correlation ID for logging
            
        Returns:
            str: ID of created document
            
        Raises:
            Exception: If creation fails
        """
        try:
            logger.info(
                f"Creating document in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={"collection": self.collection_name}
            )
            
            result = await self.collection.insert_one(document)
            
            logger.info(
                f"Document created successfully in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "documentId": str(result.inserted_id)
                }
            )
            
            return str(result.inserted_id)
        
        except Exception as e:
            logger.error(
                f"Failed to create document in {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={"collection": self.collection_name}
            )
            raise
    
    async def find_by_id(
        self,
        document_id: str,
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a document by ID.
        
        Args:
            document_id: Document ID to find
            correlation_id: Optional correlation ID for logging
            
        Returns:
            Optional[Dict]: Document if found, None otherwise
        """
        try:
            logger.debug(
                f"Finding document by ID in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "documentId": document_id
                }
            )
            
            document = await self.collection.find_one({"_id": ObjectId(document_id)})
            
            if document:
                logger.debug(
                    f"Document found in {self.collection_name}",
                    correlation_id=correlation_id,
                    metadata={
                        "collection": self.collection_name,
                        "documentId": document_id
                    }
                )
            else:
                logger.debug(
                    f"Document not found in {self.collection_name}",
                    correlation_id=correlation_id,
                    metadata={
                        "collection": self.collection_name,
                        "documentId": document_id
                    }
                )
            
            return document
        
        except Exception as e:
            logger.error(
                f"Error finding document in {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={
                    "collection": self.collection_name,
                    "documentId": document_id
                }
            )
            raise
    
    async def find_one(
        self,
        query: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching query.
        
        Args:
            query: MongoDB query filter
            correlation_id: Optional correlation ID for logging
            
        Returns:
            Optional[Dict]: Document if found, None otherwise
        """
        try:
            logger.debug(
                f"Finding document in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "query": query
                }
            )
            
            document = await self.collection.find_one(query)
            
            return document
        
        except Exception as e:
            logger.error(
                f"Error finding document in {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={
                    "collection": self.collection_name,
                    "query": query
                }
            )
            raise
    
    async def find_many(
        self,
        query: Dict[str, Any],
        skip: int = 0,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching query.
        
        Args:
            query: MongoDB query filter
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: Sort specification
            correlation_id: Optional correlation ID for logging
            
        Returns:
            List[Dict]: List of matching documents
        """
        try:
            logger.debug(
                f"Finding documents in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "query": query,
                    "skip": skip,
                    "limit": limit
                }
            )
            
            cursor = self.collection.find(query).skip(skip)
            
            if limit:
                cursor = cursor.limit(limit)
            
            if sort:
                cursor = cursor.sort(sort)
            
            documents = await cursor.to_list(length=limit)
            
            logger.debug(
                f"Found {len(documents)} documents in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "count": len(documents)
                }
            )
            
            return documents
        
        except Exception as e:
            logger.error(
                f"Error finding documents in {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={
                    "collection": self.collection_name,
                    "query": query
                }
            )
            raise
    
    async def update(
        self,
        document_id: str,
        update_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Update a document by ID.
        
        Args:
            document_id: Document ID to update
            update_data: Update operations (should include $set, $push, etc.)
            correlation_id: Optional correlation ID for logging
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            logger.info(
                f"Updating document in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "documentId": document_id
                }
            )
            
            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)},
                update_data
            )
            
            success = result.modified_count > 0
            
            if success:
                logger.info(
                    f"Document updated successfully in {self.collection_name}",
                    correlation_id=correlation_id,
                    metadata={
                        "collection": self.collection_name,
                        "documentId": document_id
                    }
                )
            else:
                logger.warning(
                    f"No document modified in {self.collection_name}",
                    correlation_id=correlation_id,
                    metadata={
                        "collection": self.collection_name,
                        "documentId": document_id
                    }
                )
            
            return success
        
        except Exception as e:
            logger.error(
                f"Error updating document in {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={
                    "collection": self.collection_name,
                    "documentId": document_id
                }
            )
            raise
    
    async def delete(self, document_id: str, correlation_id: Optional[str] = None) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: Document ID to delete
            correlation_id: Optional correlation ID for logging
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            logger.info(
                f"Deleting document from {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "documentId": document_id
                }
            )
            
            result = await self.collection.delete_one({"_id": ObjectId(document_id)})
            
            success = result.deleted_count > 0
            
            if success:
                logger.info(
                    f"Document deleted successfully from {self.collection_name}",
                    correlation_id=correlation_id,
                    metadata={
                        "collection": self.collection_name,
                        "documentId": document_id
                    }
                )
            else:
                logger.warning(
                    f"No document deleted from {self.collection_name}",
                    correlation_id=correlation_id,
                    metadata={
                        "collection": self.collection_name,
                        "documentId": document_id
                    }
                )
            
            return success
        
        except Exception as e:
            logger.error(
                f"Error deleting document from {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={
                    "collection": self.collection_name,
                    "documentId": document_id
                }
            )
            raise
    
    async def count(self, query: Dict[str, Any], correlation_id: Optional[str] = None) -> int:
        """
        Count documents matching query.
        
        Args:
            query: MongoDB query filter
            correlation_id: Optional correlation ID for logging
            
        Returns:
            int: Number of matching documents
        """
        try:
            count = await self.collection.count_documents(query)
            
            logger.debug(
                f"Counted {count} documents in {self.collection_name}",
                correlation_id=correlation_id,
                metadata={
                    "collection": self.collection_name,
                    "count": count
                }
            )
            
            return count
        
        except Exception as e:
            logger.error(
                f"Error counting documents in {self.collection_name}",
                correlation_id=correlation_id,
                error=e,
                metadata={"collection": self.collection_name}
            )
            raise
    
    async def exists(self, query: Dict[str, Any], correlation_id: Optional[str] = None) -> bool:
        """
        Check if a document exists.
        
        Args:
            query: MongoDB query filter
            correlation_id: Optional correlation ID for logging
            
        Returns:
            bool: True if exists, False otherwise
        """
        count = await self.count(query, correlation_id)
        return count > 0
