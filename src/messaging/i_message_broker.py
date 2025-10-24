"""
Message Broker Interface
Defines the contract for all message broker implementations (RabbitMQ, Kafka, etc.)
This abstraction allows easy switching between different message brokers without changing business logic.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any


class IMessageBroker(ABC):
    """Abstract base class for message broker implementations"""

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the message broker
        """
        pass

    @abstractmethod
    async def consume(self, queue_name: str, handler: Callable) -> None:
        """
        Start consuming messages from configured queues/topics
        
        Args:
            queue_name: Name of the queue to consume from
            handler: Async callback function to process messages
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to the message broker
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the broker connection is healthy
        
        Returns:
            True if connected and ready, False otherwise
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get queue/topic statistics (optional, for monitoring)
        
        Returns:
            Dictionary with statistics
        """
        pass
