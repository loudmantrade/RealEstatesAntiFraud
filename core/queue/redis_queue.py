"""
Redis Queue Plugin

Production-ready queue implementation using Redis Streams.
Supports persistence, distributed processing, and consumer groups.
"""

import json
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from core.interfaces.queue_plugin import QueuePlugin

logger = logging.getLogger(__name__)

try:
    import redis
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed. RedisQueuePlugin will not work.")


class RedisQueuePlugin(QueuePlugin):
    """
    Redis-based queue implementation using Redis Streams.
    
    Features:
    - Persistent message storage
    - Consumer groups for load balancing
    - Acknowledgment and retry mechanism
    - Dead letter queue support
    - High throughput and low latency
    
    Requirements:
    - redis >= 4.0.0
    - Redis server >= 5.0 (for Streams support)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        consumer_group: str = "default",
        consumer_name: Optional[str] = None,
        max_pending: int = 1000,
        block_ms: int = 1000,
    ):
        """
        Initialize Redis queue plugin.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            consumer_group: Consumer group name
            consumer_name: Consumer name (auto-generated if None)
            max_pending: Maximum pending messages before blocking
            block_ms: Block duration when waiting for messages
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for RedisQueuePlugin")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"consumer-{uuid.uuid4().hex[:8]}"
        self.max_pending = max_pending
        self.block_ms = block_ms
        
        self._client: Optional[redis.Redis] = None
        self._subscriptions: Dict[str, bool] = {}
        self._stats = {
            "messages_published": 0,
            "messages_consumed": 0,
            "messages_acked": 0,
            "messages_rejected": 0,
            "active_subscriptions": 0,
            "errors": 0,
        }

    def connect(self) -> None:
        """Establish connection to Redis"""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")

    def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            # Stop all subscriptions
            for subscription_id in list(self._subscriptions.keys()):
                self._subscriptions[subscription_id] = False
            
            self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        **kwargs: Any
    ) -> str:
        """Publish message to Redis Stream"""
        if not self._client:
            raise ConnectionError("Not connected to Redis")
        
        try:
            # Serialize message
            payload = json.dumps(message)
            
            # Add to stream
            message_id = self._client.xadd(
                topic,
                {"payload": payload, "timestamp": time.time()},
                maxlen=kwargs.get("maxlen", 10000),  # Limit stream size
            )
            
            self._stats["messages_published"] += 1
            logger.debug(f"Published message {message_id} to topic {topic}")
            
            return message_id
            
        except RedisError as e:
            logger.error(f"Failed to publish message: {e}")
            self._stats["errors"] += 1
            raise

    def subscribe(
        self,
        topic: str,
        callback: Callable[[Dict[str, Any]], None],
        **kwargs: Any
    ) -> str:
        """Subscribe to Redis Stream with consumer group"""
        if not self._client:
            raise ConnectionError("Not connected to Redis")
        
        subscription_id = str(uuid.uuid4())
        
        try:
            # Create consumer group if it doesn't exist
            try:
                self._client.xgroup_create(
                    topic,
                    self.consumer_group,
                    id="0",
                    mkstream=True
                )
                logger.info(f"Created consumer group {self.consumer_group} for topic {topic}")
            except RedisError as e:
                # Group might already exist
                if "BUSYGROUP" not in str(e):
                    raise
            
            # Start consuming in background
            self._subscriptions[subscription_id] = True
            self._stats["active_subscriptions"] += 1
            
            # Note: In production, this should be handled by a separate worker process
            # For now, we'll use a simple polling approach
            import threading
            thread = threading.Thread(
                target=self._consume_loop,
                args=(topic, subscription_id, callback),
                daemon=True
            )
            thread.start()
            
            logger.info(f"Subscribed to topic {topic} with ID {subscription_id}")
            return subscription_id
            
        except RedisError as e:
            logger.error(f"Failed to subscribe: {e}")
            self._stats["errors"] += 1
            raise

    def _consume_loop(
        self,
        topic: str,
        subscription_id: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Consumer loop for processing messages"""
        while self._subscriptions.get(subscription_id, False):
            try:
                # Read messages from stream
                messages = self._client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {topic: ">"},
                    count=10,
                    block=self.block_ms
                )
                
                if not messages:
                    continue
                
                for stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            # Deserialize payload
                            payload = json.loads(fields["payload"])
                            
                            # Process message
                            callback(payload)
                            
                            # Acknowledge
                            self.acknowledge(message_id)
                            self._stats["messages_consumed"] += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}")
                            self._stats["errors"] += 1
                            self.reject(message_id, requeue=False)
                
            except RedisError as e:
                logger.error(f"Consumer error: {e}")
                self._stats["errors"] += 1
                time.sleep(1.0)

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topic"""
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id] = False
            del self._subscriptions[subscription_id]
            self._stats["active_subscriptions"] -= 1
            logger.info(f"Unsubscribed {subscription_id}")

    def acknowledge(self, message_id: str) -> None:
        """Acknowledge message processing"""
        if not self._client:
            return
        
        try:
            # Extract topic from message_id format: "topic-123-456"
            topic = message_id.split("-")[0] if "-" in message_id else message_id
            
            self._client.xack(topic, self.consumer_group, message_id)
            self._stats["messages_acked"] += 1
            logger.debug(f"Acknowledged message {message_id}")
            
        except RedisError as e:
            logger.error(f"Failed to acknowledge message: {e}")
            self._stats["errors"] += 1

    def reject(self, message_id: str, requeue: bool = True) -> None:
        """Reject message"""
        if not self._client:
            return
        
        try:
            if not requeue:
                # Move to dead letter queue
                topic = message_id.split("-")[0] if "-" in message_id else message_id
                dlq_topic = f"{topic}:dlq"
                
                # Get message details
                pending = self._client.xpending_range(
                    topic,
                    self.consumer_group,
                    min=message_id,
                    max=message_id,
                    count=1
                )
                
                if pending:
                    # Move to DLQ and acknowledge original
                    self._client.xadd(dlq_topic, {"message_id": message_id, "reason": "rejected"})
                    self._client.xack(topic, self.consumer_group, message_id)
                    
            self._stats["messages_rejected"] += 1
            logger.debug(f"Rejected message {message_id}, requeue={requeue}")
            
        except RedisError as e:
            logger.error(f"Failed to reject message: {e}")
            self._stats["errors"] += 1

    def get_queue_size(self, topic: str) -> int:
        """Get stream length"""
        if not self._client:
            return 0
        
        try:
            return self._client.xlen(topic)
        except RedisError:
            return 0

    def purge_queue(self, topic: str) -> int:
        """Delete all messages from stream"""
        if not self._client:
            return 0
        
        try:
            count = self._client.xlen(topic)
            self._client.delete(topic)
            logger.info(f"Purged {count} messages from topic {topic}")
            return count
        except RedisError as e:
            logger.error(f"Failed to purge queue: {e}")
            return 0

    def create_topic(self, topic: str, **kwargs: Any) -> None:
        """Create stream (happens automatically on first xadd)"""
        logger.info(f"Topic {topic} will be created on first publish")

    def delete_topic(self, topic: str) -> None:
        """Delete stream"""
        if not self._client:
            return
        
        try:
            self._client.delete(topic)
            logger.info(f"Deleted topic {topic}")
        except RedisError as e:
            logger.error(f"Failed to delete topic: {e}")

    def list_topics(self) -> List[str]:
        """List all streams"""
        if not self._client:
            return []
        
        try:
            # Get all keys and filter streams
            keys = self._client.keys("*")
            streams = []
            for key in keys:
                if self._client.type(key) == "stream":
                    streams.append(key)
            return streams
        except RedisError:
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return dict(self._stats)

    def is_connected(self) -> bool:
        """Check connection status"""
        if not self._client:
            return False
        
        try:
            self._client.ping()
            return True
        except RedisError:
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        if not self._client:
            return {
                "status": "unhealthy",
                "latency_ms": -1,
                "details": {"error": "Not connected"}
            }
        
        try:
            start = time.time()
            self._client.ping()
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "details": {
                    "connected": True,
                    "host": self.host,
                    "port": self.port,
                    "statistics": self.get_statistics(),
                }
            }
        except RedisError as e:
            return {
                "status": "unhealthy",
                "latency_ms": -1,
                "details": {"error": str(e)}
            }
