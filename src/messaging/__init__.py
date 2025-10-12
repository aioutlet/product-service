"""
Messaging module for inventory service
Provides message broker abstraction for RabbitMQ, Kafka, etc.
"""

from .i_message_broker import IMessageBroker
from .rabbitmq_broker import RabbitMQBroker
from .kafka_broker import KafkaBroker
from .message_broker_factory import MessageBrokerFactory

__all__ = [
    "IMessageBroker",
    "RabbitMQBroker",
    "KafkaBroker",
    "MessageBrokerFactory",
]
