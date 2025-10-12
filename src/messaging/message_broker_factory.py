"""
Message Broker Factory
Creates the appropriate message broker instance based on configuration
"""

import os
import logging
from .i_message_broker import IMessageBroker
from .rabbitmq_broker import RabbitMQBroker
from .kafka_broker import KafkaBroker

logger = logging.getLogger(__name__)


class MessageBrokerFactory:
    """Factory for creating message broker instances"""

    @staticmethod
    def create() -> IMessageBroker:
        """
        Create a message broker instance based on MESSAGE_BROKER_TYPE environment variable
        
        Returns:
            IMessageBroker implementation
        """
        broker_type = os.getenv("MESSAGE_BROKER_TYPE", "rabbitmq").lower()
        
        logger.info(f"Creating message broker: {broker_type}")

        if broker_type == "rabbitmq":
            rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
            queue_name = os.getenv("MESSAGE_BROKER_QUEUE", "inventory-service.queue")
            
            return RabbitMQBroker(rabbitmq_url, queue_name)

        elif broker_type == "kafka":
            # Parse Kafka configuration
            brokers = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
            topics = os.getenv("KAFKA_TOPICS", "aioutlet.events").split(",")
            group_id = os.getenv("KAFKA_GROUP_ID", "inventory-service-group")
            
            return KafkaBroker(brokers, topics, group_id)

        else:
            raise ValueError(
                f"Unsupported message broker type: {broker_type}. "
                f"Supported types: rabbitmq, kafka"
            )
