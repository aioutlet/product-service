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
    async def start_consuming(self) -> None:
        """
        Start consuming messages from configured queues/topics
        """
        pass

    @abstractmethod
    def register_event_handler(
        self, event_type: str, handler: Callable[[Dict[str, Any], str], None]
    ) -> None:
        """
        Register event handler for specific event types
        
        Args:
            event_type: The type of event to handle
            handler: Function to process the event (eventData, correlationId) -> None
        """
        pass

    @abstractmethod
    async def close(self) -> None:
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
