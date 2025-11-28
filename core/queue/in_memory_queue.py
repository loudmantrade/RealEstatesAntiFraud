"""
In-Memory Queue Plugin

Simple in-memory queue implementation for development and testing.
Not suitable for production use - messages are not persisted.
"""

import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional

from core.interfaces.queue_plugin import QueuePlugin

logger = logging.getLogger(__name__)


class InMemoryQueuePlugin(QueuePlugin):
    """
    In-memory queue implementation for development and testing.

    Features:
    - Thread-safe operations
    - Basic pub/sub functionality
    - Message acknowledgment
    - Dead letter queue for failed messages

    Limitations:
    - No persistence (data lost on restart)
    - No distributed support
    - Limited scalability
    """

    def __init__(self):
        self._connected = False
        self._queues: Dict[str, deque] = defaultdict(deque)
        self._subscribers: Dict[str, List[tuple]] = defaultdict(list)
        self._pending_acks: Dict[str, Dict[str, Any]] = {}
        self._dead_letter: deque = deque()
        self._lock = threading.RLock()
        self._stats = {
            "messages_published": 0,
            "messages_consumed": 0,
            "messages_acked": 0,
            "messages_rejected": 0,
            "active_subscriptions": 0,
            "errors": 0,
        }
        self._worker_threads: Dict[str, threading.Thread] = {}
        self._stop_flags: Dict[str, threading.Event] = {}

    def connect(self) -> None:
        """Establish connection (no-op for in-memory)"""
        if self._connected:
            logger.warning("Already connected")
            return

        self._connected = True
        logger.info("In-memory queue connected")

    def disconnect(self) -> None:
        """Close connection and stop all workers"""
        if not self._connected:
            return

        # Stop all worker threads
        for topic, stop_flag in self._stop_flags.items():
            stop_flag.set()

        # Wait for threads to finish
        for thread in self._worker_threads.values():
            thread.join(timeout=5.0)

        self._connected = False
        logger.info("In-memory queue disconnected")

    def publish(self, topic: str, message: Dict[str, Any], **kwargs: Any) -> str:
        """Publish a message to a queue"""
        if not self._connected:
            raise ConnectionError("Not connected to queue")

        message_id = str(uuid.uuid4())
        envelope = {
            "message_id": message_id,
            "topic": topic,
            "payload": message,
            "timestamp": time.time(),
            "metadata": kwargs,
        }

        with self._lock:
            self._queues[topic].append(envelope)
            self._stats["messages_published"] += 1

        logger.debug(f"Published message {message_id} to topic {topic}")
        return message_id

    def subscribe(
        self, topic: str, callback: Callable[[Dict[str, Any]], None], **kwargs: Any
    ) -> str:
        """Subscribe to a topic with a callback"""
        if not self._connected:
            raise ConnectionError("Not connected to queue")

        subscription_id = str(uuid.uuid4())

        with self._lock:
            self._subscribers[topic].append((subscription_id, callback, kwargs))
            self._stats["active_subscriptions"] += 1

        # Start worker thread for this subscription
        stop_flag = threading.Event()
        self._stop_flags[subscription_id] = stop_flag

        worker = threading.Thread(
            target=self._worker_loop,
            args=(topic, subscription_id, callback, stop_flag),
            daemon=True,
            name=f"worker-{topic}-{subscription_id[:8]}",
        )
        self._worker_threads[subscription_id] = worker
        worker.start()

        logger.info(f"Subscribed to topic {topic} with ID {subscription_id}")
        return subscription_id

    def _worker_loop(
        self,
        topic: str,
        subscription_id: str,
        callback: Callable[[Dict[str, Any]], None],
        stop_flag: threading.Event,
    ) -> None:
        """Worker thread that processes messages from a queue"""
        logger.info(f"Worker started for subscription {subscription_id}")

        while not stop_flag.is_set():
            try:
                # Try to get a message
                envelope = None
                with self._lock:
                    if self._queues[topic]:
                        envelope = self._queues[topic].popleft()

                if envelope:
                    message_id = envelope["message_id"]
                    payload = envelope["payload"]

                    # Store for acknowledgment
                    self._pending_acks[message_id] = envelope

                    try:
                        # Process message
                        callback(payload)
                        self._stats["messages_consumed"] += 1

                        # Auto-acknowledge if not explicitly rejected
                        if message_id in self._pending_acks:
                            self.acknowledge(message_id)
                    except Exception as e:
                        logger.error(f"Error processing message {message_id}: {e}")
                        self._stats["errors"] += 1
                        self.reject(message_id, requeue=False)
                else:
                    # No messages, sleep briefly
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Worker error: {e}")
                self._stats["errors"] += 1
                time.sleep(1.0)

        logger.info(f"Worker stopped for subscription {subscription_id}")

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a topic"""
        # Stop worker thread
        if subscription_id in self._stop_flags:
            self._stop_flags[subscription_id].set()

        if subscription_id in self._worker_threads:
            self._worker_threads[subscription_id].join(timeout=5.0)
            del self._worker_threads[subscription_id]
            del self._stop_flags[subscription_id]

        # Remove from subscribers
        with self._lock:
            for topic, subs in self._subscribers.items():
                self._subscribers[topic] = [
                    (sid, cb, kw) for sid, cb, kw in subs if sid != subscription_id
                ]
            self._stats["active_subscriptions"] -= 1

        logger.info(f"Unsubscribed {subscription_id}")

    def acknowledge(self, message_id: str) -> None:
        """Acknowledge successful processing"""
        with self._lock:
            if message_id in self._pending_acks:
                del self._pending_acks[message_id]
                self._stats["messages_acked"] += 1
                logger.debug(f"Acknowledged message {message_id}")

    def reject(self, message_id: str, requeue: bool = True) -> None:
        """Reject a message"""
        with self._lock:
            if message_id in self._pending_acks:
                envelope = self._pending_acks.pop(message_id)
                self._stats["messages_rejected"] += 1

                if requeue:
                    # Put back at the end of the queue
                    topic = envelope["topic"]
                    self._queues[topic].append(envelope)
                    logger.debug(f"Requeued message {message_id}")
                else:
                    # Move to dead letter queue
                    self._dead_letter.append(envelope)
                    logger.debug(f"Moved message {message_id} to dead letter queue")

    def get_queue_size(self, topic: str) -> int:
        """Get number of pending messages"""
        with self._lock:
            return len(self._queues[topic])

    def purge_queue(self, topic: str) -> int:
        """Delete all messages from a queue"""
        with self._lock:
            count = len(self._queues[topic])
            self._queues[topic].clear()
            logger.info(f"Purged {count} messages from topic {topic}")
            return count

    def create_topic(self, topic: str, **kwargs: Any) -> None:
        """Create a new topic (no-op for in-memory)"""
        with self._lock:
            if topic not in self._queues:
                self._queues[topic] = deque()
                logger.info(f"Created topic {topic}")

    def delete_topic(self, topic: str) -> None:
        """Delete a topic"""
        with self._lock:
            if topic in self._queues:
                del self._queues[topic]
            if topic in self._subscribers:
                del self._subscribers[topic]
            logger.info(f"Deleted topic {topic}")

    def list_topics(self) -> List[str]:
        """List all topics"""
        with self._lock:
            return list(self._queues.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self._lock:
            return {
                **self._stats,
                "dead_letter_size": len(self._dead_letter),
                "pending_acks": len(self._pending_acks),
                "total_queues": len(self._queues),
            }

    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        status = "healthy" if self._connected else "unhealthy"

        return {
            "status": status,
            "latency_ms": 0.0,  # No network latency for in-memory
            "details": {
                "connected": self._connected,
                "active_workers": len(self._worker_threads),
                "statistics": self.get_statistics(),
            },
        }

    def get_dead_letter_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue"""
        with self._lock:
            return list(self._dead_letter)[-limit:]

    def clear_dead_letter_queue(self) -> int:
        """Clear dead letter queue"""
        with self._lock:
            count = len(self._dead_letter)
            self._dead_letter.clear()
            logger.info(f"Cleared {count} messages from dead letter queue")
            return count
