"""
Message Queue Plugin Interface

Defines the abstract interface for message queue implementations.
Supports multiple backends: Redis, RabbitMQ, Kafka, AWS SQS, etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List


class QueuePlugin(ABC):
    """
    Abstract base class for message queue plugins.

    Provides unified interface for different message queue systems,
    enabling easy switching between backends without changing application code.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the message queue.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the message queue.

        Should clean up resources and ensure graceful shutdown.
        """
        pass

    @abstractmethod
    def publish(self, topic: str, message: Dict[str, Any], **kwargs: Any) -> str:
        """
        Publish a message to a topic/queue.

        Args:
            topic: Topic/queue name
            message: Message payload (will be JSON serialized)
            **kwargs: Backend-specific options (e.g., priority, delay)

        Returns:
            Message ID or acknowledgment token

        Raises:
            PublishError: If message cannot be published
        """
        pass

    @abstractmethod
    def subscribe(
        self, topic: str, callback: Callable[[Dict[str, Any]], None], **kwargs: Any
    ) -> str:
        """
        Subscribe to a topic/queue and process messages.

        Args:
            topic: Topic/queue name to subscribe to
            callback: Function to call for each message
            **kwargs: Backend-specific options (e.g., consumer_group)

        Returns:
            Subscription ID

        Raises:
            SubscriptionError: If subscription fails
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from a topic/queue.

        Args:
            subscription_id: ID returned by subscribe()
        """
        pass

    @abstractmethod
    def acknowledge(self, message_id: str) -> None:
        """
        Acknowledge successful processing of a message.

        Args:
            message_id: ID of the message to acknowledge
        """
        pass

    @abstractmethod
    def reject(self, message_id: str, requeue: bool = True) -> None:
        """
        Reject a message (processing failed).

        Args:
            message_id: ID of the message to reject
            requeue: Whether to requeue the message for retry
        """
        pass

    @abstractmethod
    def get_queue_size(self, topic: str) -> int:
        """
        Get the number of messages in a queue.

        Args:
            topic: Topic/queue name

        Returns:
            Number of pending messages
        """
        pass

    @abstractmethod
    def purge_queue(self, topic: str) -> int:
        """
        Delete all messages from a queue.

        Args:
            topic: Topic/queue name

        Returns:
            Number of messages deleted
        """
        pass

    @abstractmethod
    def create_topic(self, topic: str, **kwargs: Any) -> None:
        """
        Create a new topic/queue.

        Args:
            topic: Topic/queue name
            **kwargs: Backend-specific configuration
        """
        pass

    @abstractmethod
    def delete_topic(self, topic: str) -> None:
        """
        Delete a topic/queue.

        Args:
            topic: Topic/queue name
        """
        pass

    @abstractmethod
    def list_topics(self) -> List[str]:
        """
        List all available topics/queues.

        Returns:
            List of topic/queue names
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get queue statistics and metrics.

        Returns:
            Dictionary containing statistics like:
            - messages_published
            - messages_consumed
            - active_subscriptions
            - errors
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the queue system.

        Returns:
            Health status dictionary with:
            - status: "healthy" | "degraded" | "unhealthy"
            - latency_ms: Connection latency
            - details: Additional diagnostic info
        """
        pass
