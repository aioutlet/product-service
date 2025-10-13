"""
Product Service Consumer - Message Consumer
Processes async events from message broker
"""
import sys
import os
import signal
import asyncio

# Add the parent directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from src.shared.observability import logger
from src.shared.messaging.message_broker_factory import MessageBrokerFactory
from src.consumer.handlers.handler_registry import get_handler

# Load environment variables
load_dotenv()

class ProductConsumer:
    """Consumer process for consuming and processing messages"""
    
    def __init__(self):
        self.broker = None
        self.is_running = True
        
    async def process_message(self, message_data: dict, correlation_id: str = None):
        """
        Process incoming message by routing to appropriate handler
        
        Args:
            message_data: The message payload containing eventType and data
            correlation_id: Optional correlation ID for tracing
        """
        try:
            event_type = message_data.get('eventType')
            event_data = message_data.get('data', {})
            
            if not event_type:
                logger.error("Message missing eventType field", metadata={
                    "correlationId": correlation_id,
                    "message": message_data
                })
                return
            
            # Get handler for this event type
            handler = get_handler(event_type)
            
            if handler:
                logger.info(f"Processing event: {event_type}", metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type
                })
                await handler(event_data, correlation_id)
            else:
                logger.warning(f"No handler registered for event type: {event_type}", metadata={
                    "correlationId": correlation_id,
                    "eventType": event_type
                })
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", metadata={
                "correlationId": correlation_id,
                "error": str(e),
                "message": message_data
            })
            raise
    
    async def start(self):
        """Start the consumer and begin consuming messages"""
        try:
            logger.info("Product Consumer starting...")
            
            # Create message broker instance
            broker_type = os.getenv('MESSAGE_BROKER_TYPE', 'rabbitmq')
            queue_name = os.getenv('MESSAGE_BROKER_QUEUE', 'product-service.queue')
            
            logger.info(f"Initializing {broker_type} message broker", metadata={
                "brokerType": broker_type,
                "queue": queue_name
            })
            
            self.broker = MessageBrokerFactory.create(broker_type)
            
            # Connect to broker
            await self.broker.connect()
            
            # Start consuming messages
            logger.info(f"Consumer started, consuming from queue: {queue_name}")
            await self.broker.consume(queue_name, self.process_message)
            
        except Exception as e:
            logger.error(f"Failed to start consumer: {str(e)}", metadata={
                "error": str(e)
            })
            raise
    
    async def stop(self):
        """Gracefully stop the consumer"""
        logger.info("Stopping Product Consumer...")
        self.is_running = False
        
        if self.broker:
            try:
                await self.broker.disconnect()
                logger.info("Message broker disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting broker: {str(e)}")
        
        logger.info("Product Consumer stopped")


# Global consumer instance
consumer = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    if consumer:
        asyncio.create_task(consumer.stop())

async def main():
    """Main entry point for the consumer"""
    global consumer
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start consumer
    consumer = ProductConsumer()
    
    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
