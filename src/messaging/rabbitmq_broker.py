"""
RabbitMQ Broker Implementation
Implements the IMessageBroker interface for RabbitMQ using aio-pika for async support
"""

import aio_pika
import json
import logging
from typing import Callable, Dict, Any, Optional
from .i_message_broker import IMessageBroker

logger = logging.getLogger(__name__)


class RabbitMQBroker(IMessageBroker):
    """RabbitMQ implementation of IMessageBroker with async support"""

    def __init__(self, rabbitmq_url: str, queue_name: str):
        """
        Initialize RabbitMQ broker
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Name of the queue to consume from
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.message_handler: Optional[Callable] = None
        self._is_connected = False

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ...")
            
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                heartbeat=600
            )
            
            self.channel = await self.connection.channel()
            
            # Set QoS - prefetch count
            await self.channel.set_qos(prefetch_count=10)
            
            # Declare queue (idempotent)
            self.queue = await self.channel.declare_queue(
                self.queue_name, 
                durable=True
            )
            
            self._is_connected = True
            logger.info(f"✅ RabbitMQ connected successfully")
            logger.info(f"📥 Queue: {self.queue_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            self._is_connected = False
            raise

    async def consume(self, queue_name: str, handler: Callable) -> None:
        """
        Start consuming messages from RabbitMQ
        
        Args:
            queue_name: Name of the queue to consume from
            handler: Async callback function to process messages
        """
        if not self.queue:
            raise RuntimeError("Queue not initialized. Call connect() first.")

        self.message_handler = handler
        logger.info("🚀 Starting message consumption...")
        logger.info(f"🎯 Message consumer started - listening for events on queue: {self.queue_name}")

        try:
            # Start consuming messages
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await self._handle_message(message)
        except Exception as e:
            logger.error(f"Error while consuming: {e}")
            raise

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        """Handle incoming message"""
        correlation_id = message.correlation_id or "unknown"
        message_id = message.message_id or "unknown"

        try:
            # Parse message
            event_data = json.loads(message.body.decode())
            
            # Handle message broker format: { topic, data } -> { eventType, ...data }
            if "topic" in event_data and "data" in event_data:
                event_data = {
                    "eventType": event_data["topic"],
                    **event_data["data"]
                }

            event_type = event_data.get("eventType", "unknown")

            logger.info(f"📨 Received event: {event_type} (correlationId: {correlation_id})")

            # Call the registered handler
            if self.message_handler:
                await self.message_handler(event_data, correlation_id)
            else:
                logger.warning(f"⚠️ No message handler registered")

            logger.debug(f"✅ Message processed successfully (messageId: {message_id})")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse message JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            raise

    async def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        try:
            logger.info("🛑 Stopping RabbitMQ broker...")
            
            if self.channel:
                await self.channel.close()
                logger.info("📦 Channel closed")

            if self.connection:
                await self.connection.close()
                logger.info("🔌 RabbitMQ connection closed")

            self._is_connected = False
        except Exception as e:
            logger.error(f"❌ Error closing RabbitMQ connection: {e}")
            raise

    def is_healthy(self) -> bool:
        """Check if broker connection is healthy"""
        return (
            self._is_connected
            and self.connection is not None
            and not self.connection.is_closed
        )

    async def get_stats(self) -> Dict[str, Any]:
        """Get RabbitMQ statistics"""
        if not self.queue:
            raise RuntimeError("Queue not initialized")

        try:
            # Get queue stats
            queue_info = await self.queue.channel.queue_declare(
                self.queue_name, 
                passive=True
            )
            
            return {
                "queue": self.queue_name,
                "message_count": queue_info.message_count,
                "consumer_count": queue_info.consumer_count,
                "connected": self._is_connected,
            }
        except Exception as e:
            logger.error(f"❌ Error getting queue stats: {e}")
            return {
                "queue": self.queue_name,
                "error": str(e),
                "connected": self._is_connected,
            }
