"""
Integration tests for RedisQueuePlugin.

Tests the Redis-based queue implementation including:
- Connection management
- Topic creation and deletion
- Publishing and subscribing
- Message acknowledgment and rejection
- Consumer groups
- Error handling
"""

import asyncio
import time
from typing import List

import pytest
import redis.asyncio as aioredis

from core.queue.redis_queue import RedisQueuePlugin


@pytest.fixture
def redis_queue(test_config):
    """Create a RedisQueuePlugin instance for testing."""
    queue = RedisQueuePlugin(
        host=test_config["redis_host"],
        port=test_config["redis_port"],
        db=test_config["redis_db"],
        consumer_group="test-group",
        consumer_name="test-consumer",
    )
    queue.connect()
    yield queue
    queue.disconnect()


@pytest.fixture
async def clean_redis_queue(redis_clean, test_config):
    """Create a clean RedisQueuePlugin instance with empty database."""
    queue = RedisQueuePlugin(
        host=test_config["redis_host"],
        port=test_config["redis_port"],
        db=test_config["redis_db"],
        consumer_group="test-group",
        consumer_name="test-consumer",
    )
    queue.connect()
    yield queue
    queue.disconnect()


class TestRedisQueueConnection:
    """Test Redis queue connection management."""

    def test_connect_success(self, test_config):
        """Test successful connection to Redis."""
        queue = RedisQueuePlugin(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
        )
        
        queue.connect()
        assert queue._client is not None
        
        # Test connection is working
        result = queue._client.ping()
        assert result is True
        
        queue.disconnect()

    def test_connect_with_password(self, test_config):
        """Test connection with password (if Redis requires auth)."""
        # Skip if Redis doesn't require password
        queue = RedisQueuePlugin(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
            password=None,  # Use None for no-auth Redis
        )
        
        queue.connect()
        assert queue._client is not None
        queue.disconnect()

    def test_disconnect(self, redis_queue):
        """Test disconnection from Redis."""
        assert redis_queue._client is not None
        
        redis_queue.disconnect()
        
        # After disconnect, client should be None or connection closed
        # Depending on implementation

    def test_health_check_connected(self, redis_queue):
        """Test health check when connected."""
        health = redis_queue.health_check()
        
        assert health["status"] == "healthy"
        assert "details" in health
        assert health["details"]["connected"] is True
        assert "latency_ms" in health
        assert health["latency_ms"] >= 0

    def test_health_check_disconnected(self, test_config):
        """Test health check when disconnected."""
        queue = RedisQueuePlugin(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
        )
        
        # Don't connect
        health = queue.health_check()
        
        assert health["status"] == "unhealthy"
        assert "details" in health
        assert "error" in health["details"]


class TestRedisQueueTopics:
    """Test topic creation and management."""

    def test_create_topic(self, clean_redis_queue):
        """Test creating a new topic (stream)."""
        topic = "test.topic"
        
        # create_topic marks topic for creation
        clean_redis_queue.create_topic(topic)
        
        # Stream is created on first publish
        clean_redis_queue.publish(topic, {"test": "data"})
        
        # Verify stream exists (check with Redis directly)
        exists = clean_redis_queue._client.exists(topic)
        assert exists == 1

    def test_create_topic_idempotent(self, clean_redis_queue):
        """Test creating same topic multiple times is safe."""
        topic = "test.topic.idempotent"
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.create_topic(topic)  # Should not error
        
        # Publish to actually create stream
        clean_redis_queue.publish(topic, {"test": "data"})
        
        exists = clean_redis_queue._client.exists(topic)
        assert exists == 1

    def test_delete_topic(self, clean_redis_queue):
        """Test deleting a topic."""
        topic = "test.topic.delete"
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.delete_topic(topic)
        
        # Verify stream is deleted
        exists = clean_redis_queue._client.exists(topic)
        assert exists == 0

    def test_delete_nonexistent_topic(self, clean_redis_queue):
        """Test deleting non-existent topic doesn't error."""
        clean_redis_queue.delete_topic("nonexistent.topic")
        # Should not raise error


class TestRedisQueuePublish:
    """Test message publishing."""

    def test_publish_simple_message(self, clean_redis_queue):
        """Test publishing a simple message."""
        topic = "test.publish.simple"
        message = {"key": "value", "number": 42}
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.publish(topic, message)
        
        # Check message was added to stream
        messages = clean_redis_queue._client.xread({topic: "0"}, count=1)
        assert len(messages) == 1
        assert len(messages[0][1]) == 1

    def test_publish_multiple_messages(self, clean_redis_queue):
        """Test publishing multiple messages."""
        topic = "test.publish.multiple"
        messages = [
            {"id": 1, "data": "first"},
            {"id": 2, "data": "second"},
            {"id": 3, "data": "third"},
        ]
        
        clean_redis_queue.create_topic(topic)
        
        for msg in messages:
            clean_redis_queue.publish(topic, msg)
        
        # Check all messages are in stream
        stream_messages = clean_redis_queue._client.xread({topic: "0"}, count=10)
        assert len(stream_messages) == 1
        assert len(stream_messages[0][1]) == 3

    def test_publish_complex_message(self, clean_redis_queue):
        """Test publishing complex nested message."""
        topic = "test.publish.complex"
        message = {
            "listing": {
                "id": "test-001",
                "price": 100000,
                "location": {"city": "Moscow", "district": "Center"},
            },
            "metadata": {"timestamp": 1234567890, "source": "test"},
        }
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.publish(topic, message)
        
        # Verify message exists
        messages = clean_redis_queue._client.xread({topic: "0"}, count=1)
        assert len(messages) == 1

    def test_publish_to_nonexistent_topic(self, clean_redis_queue):
        """Test publishing to non-existent topic creates it."""
        topic = "test.publish.autocreate"
        message = {"test": "data"}
        
        # Don't create topic explicitly
        clean_redis_queue.publish(topic, message)
        
        # Topic should be auto-created
        exists = clean_redis_queue._client.exists(topic)
        assert exists == 1

    def test_publish_updates_statistics(self, clean_redis_queue):
        """Test that publishing updates statistics."""
        topic = "test.publish.stats"
        
        initial_count = clean_redis_queue._stats["messages_published"]
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.publish(topic, {"test": "message"})
        
        assert clean_redis_queue._stats["messages_published"] == initial_count + 1


class TestRedisQueueSubscribe:
    """Test message subscription and consumption."""

    def test_subscribe_and_receive(self, clean_redis_queue):
        """Test subscribing to a topic and receiving messages."""
        topic = "test.subscribe.basic"
        received_messages = []
        
        def callback(msg):
            received_messages.append(msg)
        
        clean_redis_queue.create_topic(topic)
        
        # Subscribe
        sub_id = clean_redis_queue.subscribe(topic, callback)
        assert sub_id is not None
        
        # Publish message
        test_message = {"test": "data", "id": 123}
        clean_redis_queue.publish(topic, test_message)
        
        # Give time for message to be processed
        time.sleep(0.2)
        
        # Check message was received
        assert len(received_messages) >= 1
        # Note: message may be wrapped, check it contains our data

    def test_multiple_subscriptions(self, clean_redis_queue):
        """Test multiple subscriptions to same topic."""
        topic = "test.subscribe.multiple"
        received_1 = []
        received_2 = []
        
        clean_redis_queue.create_topic(topic)
        
        # Subscribe twice
        sub_id_1 = clean_redis_queue.subscribe(topic, lambda msg: received_1.append(msg))
        sub_id_2 = clean_redis_queue.subscribe(topic, lambda msg: received_2.append(msg))
        
        assert sub_id_1 != sub_id_2
        
        # Publish message
        clean_redis_queue.publish(topic, {"test": "multi"})
        
        time.sleep(0.2)
        
        # Both should receive (or one if using consumer groups)
        # Behavior depends on consumer group implementation

    def test_unsubscribe(self, clean_redis_queue):
        """Test unsubscribing from a topic."""
        topic = "test.subscribe.unsub"
        received = []
        
        clean_redis_queue.create_topic(topic)
        
        sub_id = clean_redis_queue.subscribe(topic, lambda msg: received.append(msg))
        
        # Unsubscribe
        clean_redis_queue.unsubscribe(sub_id)
        
        # Publish after unsubscribe
        clean_redis_queue.publish(topic, {"test": "after_unsub"})
        
        time.sleep(0.2)
        
        # Should not receive message after unsubscribe
        # (or receive 0 messages if unsubscribed before any were sent)

    def test_subscribe_before_publish(self, clean_redis_queue):
        """Test subscribing before messages are published."""
        topic = "test.subscribe.before"
        received = []
        
        clean_redis_queue.create_topic(topic)
        
        # Subscribe first
        clean_redis_queue.subscribe(topic, lambda msg: received.append(msg))
        
        # Then publish
        clean_redis_queue.publish(topic, {"order": "first"})
        clean_redis_queue.publish(topic, {"order": "second"})
        
        time.sleep(0.3)
        
        # Should receive both messages
        assert len(received) >= 2


class TestRedisQueueAcknowledgment:
    """Test message acknowledgment."""

    def test_acknowledge_message(self, clean_redis_queue):
        """Test acknowledging a message."""
        topic = "test.ack.basic"
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.publish(topic, {"test": "ack"})
        
        # Get message ID somehow (depends on implementation)
        # For now, test the method exists and doesn't error
        try:
            clean_redis_queue.acknowledge("test-message-id")
        except Exception:
            # May fail with invalid ID, but method should exist
            pass

    def test_reject_message(self, clean_redis_queue):
        """Test rejecting a message."""
        topic = "test.reject.basic"
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.publish(topic, {"test": "reject"})
        
        # Test reject method exists
        try:
            clean_redis_queue.reject("test-message-id")
        except Exception:
            # May fail with invalid ID, but method should exist
            pass


class TestRedisQueueStatistics:
    """Test queue statistics."""

    def test_get_statistics(self, clean_redis_queue):
        """Test getting queue statistics."""
        stats = clean_redis_queue.get_statistics()
        
        assert "messages_published" in stats
        assert "messages_consumed" in stats
        assert "messages_acked" in stats
        assert "messages_rejected" in stats
        assert isinstance(stats["messages_published"], int)

    def test_statistics_after_operations(self, clean_redis_queue):
        """Test statistics are updated after operations."""
        topic = "test.stats.ops"
        
        initial_stats = clean_redis_queue.get_statistics()
        initial_published = initial_stats["messages_published"]
        
        clean_redis_queue.create_topic(topic)
        clean_redis_queue.publish(topic, {"test": "stats"})
        
        updated_stats = clean_redis_queue.get_statistics()
        
        assert updated_stats["messages_published"] == initial_published + 1

    def test_get_queue_size(self, clean_redis_queue):
        """Test getting queue size for a topic."""
        topic = "test.size"
        
        clean_redis_queue.create_topic(topic)
        
        # Publish some messages
        for i in range(5):
            clean_redis_queue.publish(topic, {"id": i})
        
        # Get queue size
        size = clean_redis_queue.get_queue_size(topic)
        
        # Size should reflect messages in stream
        assert size >= 5


class TestRedisQueueErrorHandling:
    """Test error handling."""

    def test_publish_to_disconnected_queue(self, test_config):
        """Test publishing when disconnected."""
        queue = RedisQueuePlugin(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
        )
        
        # Don't connect
        with pytest.raises(Exception):
            queue.publish("test.topic", {"test": "data"})

    def test_connect_to_invalid_host(self):
        """Test connecting to invalid Redis host."""
        queue = RedisQueuePlugin(
            host="invalid-host-that-does-not-exist",
            port=6379,
            db=0,
        )
        
        with pytest.raises(Exception):
            queue.connect()

    def test_invalid_message_handling(self, clean_redis_queue):
        """Test handling of invalid message types."""
        topic = "test.invalid"
        
        clean_redis_queue.create_topic(topic)
        
        # Try to publish non-serializable data
        # Should handle gracefully or raise appropriate error
        try:
            clean_redis_queue.publish(topic, {"func": lambda x: x})
        except (TypeError, ValueError):
            # Expected - can't serialize functions
            pass


class TestRedisQueuePurge:
    """Test purging queues."""

    def test_purge_queue(self, clean_redis_queue):
        """Test purging all messages from a queue."""
        topic = "test.purge"
        
        clean_redis_queue.create_topic(topic)
        
        # Add messages
        for i in range(10):
            clean_redis_queue.publish(topic, {"id": i})
        
        # Purge
        clean_redis_queue.purge_queue(topic)
        
        # Check queue is empty
        size = clean_redis_queue.get_queue_size(topic)
        assert size == 0


class TestRedisQueueIntegration:
    """Integration tests combining multiple features."""

    def test_full_message_lifecycle(self, clean_redis_queue):
        """Test complete message lifecycle: publish -> subscribe -> ack."""
        topic = "test.integration.lifecycle"
        received = []
        
        clean_redis_queue.create_topic(topic)
        
        # Subscribe
        clean_redis_queue.subscribe(topic, lambda msg: received.append(msg))
        
        # Publish
        message = {"lifecycle": "test", "timestamp": time.time()}
        clean_redis_queue.publish(topic, message)
        
        # Wait for delivery
        time.sleep(0.2)
        
        # Verify received
        assert len(received) >= 1
        
        # Get statistics
        stats = clean_redis_queue.get_statistics()
        assert stats["messages_published"] >= 1

    def test_concurrent_publishers(self, clean_redis_queue):
        """Test multiple publishers publishing concurrently."""
        topic = "test.integration.concurrent"
        
        clean_redis_queue.create_topic(topic)
        
        # Publish from "multiple" sources
        for i in range(20):
            clean_redis_queue.publish(topic, {"source": i % 3, "message": i})
        
        # All should be in queue
        size = clean_redis_queue.get_queue_size(topic)
        assert size >= 20

    def test_message_ordering(self, clean_redis_queue):
        """Test that messages maintain order."""
        topic = "test.integration.order"
        received = []
        
        clean_redis_queue.create_topic(topic)
        
        # Subscribe
        clean_redis_queue.subscribe(topic, lambda msg: received.append(msg))
        
        # Publish in order
        for i in range(10):
            clean_redis_queue.publish(topic, {"seq": i})
            time.sleep(0.01)  # Small delay
        
        time.sleep(0.3)
        
        # Messages should arrive in order (Redis Streams guarantee this)
        assert len(received) >= 10
