"""
Repository for tracking processed events to ensure idempotency
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING

from app.core.logger import logger


class ProcessedEventRepository:
    """Repository for managing processed events"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["processed_events"]
        self._indexes_created = False
    
    async def ensure_indexes(self):
        """Create indexes for processed events collection"""
        if self._indexes_created:
            return
        
        indexes = [
            IndexModel([("event_id", ASCENDING)], unique=True, name="event_id_unique"),
            IndexModel([("event_type", ASCENDING)], name="event_type_idx"),
            IndexModel([("processed_at", ASCENDING)], expireAfterSeconds=2592000, name="ttl_idx"),  # 30 days TTL
            IndexModel([("product_id", ASCENDING)], name="product_id_idx"),
        ]
        
        await self.collection.create_indexes(indexes)
        self._indexes_created = True
        logger.info("Processed events indexes created")
    
    async def is_processed(self, event_id: str) -> bool:
        """
        Check if event has already been processed
        
        Args:
            event_id: Unique event identifier
            
        Returns:
            True if event was already processed, False otherwise
        """
        result = await self.collection.find_one({"event_id": event_id})
        return result is not None
    
    async def mark_processed(
        self,
        event_id: str,
        event_type: str,
        product_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Mark an event as processed
        
        Args:
            event_id: Unique event identifier
            event_type: Type of event (review.created, review.updated, etc.)
            product_id: Product ID related to the event
            metadata: Additional metadata about the event processing
            
        Returns:
            True if successfully marked, False if already exists
        """
        try:
            document = {
                "event_id": event_id,
                "event_type": event_type,
                "product_id": product_id,
                "processed_at": datetime.now(timezone.utc),
                "metadata": metadata or {},
            }
            
            result = await self.collection.insert_one(document)
            return result.inserted_id is not None
            
        except Exception as e:
            # Duplicate key error means it was already processed
            if "duplicate key" in str(e).lower():
                logger.warning(f"Event {event_id} already processed (duplicate key)")
                return False
            raise
    
    async def get_processed_count(self, hours: int = 24) -> dict:
        """
        Get count of processed events in the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with counts by event type
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        pipeline = [
            {"$match": {"processed_at": {"$gte": since}}},
            {"$group": {
                "_id": "$event_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        
        return {
            "total": sum(r["count"] for r in results),
            "by_type": {r["_id"]: r["count"] for r in results},
            "since": since.isoformat()
        }
