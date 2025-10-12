"""
RabbitMQ Broker Implementation
Implements the IMessageBroker interface for RabbitMQ
"""

import pika
import json
import logging
from typing import Callable, Dict, Any, Optional
from .i_message_broker import IMessageBroker

logger = logging.getLogger(__name__)


class RabbitMQBroker(IMessageBroker):
    """RabbitMQ implementation of IMessageBroker"""

    def __init__(self, rabbitmq_url: str, queue_name: str):
        """
        Initialize RabbitMQ broker
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Name of the queue to consume from
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.event_handlers: Dict[str, Callable] = {}
        self._is_connected = False

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ...")
            
            # Parse connection URL
            parameters = pika.URLParameters(self.rabbitmq_url)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (idempotent)
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Set QoS - prefetch count
            self.channel.basic_qos(prefetch_count=10)
            
            self._is_connected = True
            logger.info(f"✅ RabbitMQ connected successfully")
            logger.info(f"📥 Queue: {self.queue_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            self._is_connected = False
            raise

    def register_event_handler(
        self, event_type: str, handler: Callable[[Dict[str, Any], str], None]
    ) -> None:
        """Register event handler for specific event types"""
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered event handler for: {event_type}")

    async def start_consuming(self) -> None:
        """Start consuming messages from RabbitMQ"""
        if not self.channel:
            raise RuntimeError("Channel not initialized. Call connect() first.")

        logger.info("🚀 Starting message consumption...")

        # Setup callback
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._handle_message,
            auto_ack=False
        )

        logger.info(f"🎯 Message consumer started - listening for events on queue: {self.queue_name}")

        try:
            # Start consuming (blocking call)
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Interrupted by user, stopping...")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error while consuming: {e}")
            raise

    def _handle_message(
        self,
        channel: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes
    ) -> None:
        """Handle incoming message"""
        correlation_id = properties.correlation_id or "unknown"
        message_id = properties.message_id or "unknown"

        try:
            # Parse message
            event_data = json.loads(body.decode())
            
            # Handle message broker format: { topic, data } -> { eventType, ...data }
            if "topic" in event_data and "data" in event_data:
                event_data = {
                    "eventType": event_data["topic"],
                    **event_data["data"]
                }

            event_type = event_data.get("eventType", "unknown")

            logger.info(f"📨 Received event: {event_type} (correlationId: {correlation_id})")

            # Check if there's a registered handler
            handler = self.event_handlers.get(event_type)
            if handler:
                handler(event_data, correlation_id)
            else:
                logger.warning(f"⚠️ No handler registered for event type: {event_type}")

            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"✅ Message processed successfully (messageId: {message_id})")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse message JSON: {e}")
            # Reject message - don't requeue to avoid infinite loop
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            # Reject message - don't requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    async def close(self) -> None:
        """Close RabbitMQ connection"""
        try:
            logger.info("🛑 Stopping RabbitMQ broker...")
            
            if self.channel:
                self.channel.stop_consuming()
                self.channel.close()
                logger.info("📦 Channel closed")

            if self.connection:
                self.connection.close()
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
            and self.connection.is_open
            and self.channel is not None
            and self.channel.is_open
        )

    async def get_stats(self) -> Dict[str, Any]:
        """Get RabbitMQ statistics"""
        if not self.channel:
            raise RuntimeError("Channel not initialized")

        try:
            # Get queue stats using passive declare
            queue = self.channel.queue_declare(queue=self.queue_name, passive=True)
            
            return {
                "queue": self.queue_name,
                "message_count": queue.method.message_count,
                "consumer_count": queue.method.consumer_count,
                "connected": self._is_connected,
            }
        except Exception as e:
            logger.error(f"❌ Error getting queue stats: {e}")
            return {
                "queue": self.queue_name,
                "error": str(e),
                "connected": self._is_connected,
            }
