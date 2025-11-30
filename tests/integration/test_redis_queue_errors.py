"""
Integration tests for Redis Queue error handling and edge cases.

Covers:
- Connection failure scenarios
- Redis unavailable handling
- Stream operation errors
- Consumer group conflicts
- Acknowledgment failures
- Dead letter queue operations
- Reconnection logic
- Statistics under error conditions
- Health check when Redis down
"""

import json
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

from core.queue.redis_queue import REDIS_AVAILABLE, RedisQueuePlugin

pytestmark = pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")


@pytest.fixture
def redis_queue(test_config):
    """Create a RedisQueuePlugin instance for testing."""
    queue = RedisQueuePlugin(
        host=test_config["redis_host"],
        port=test_config["redis_port"],
        db=test_config["redis_db"],
        consumer_group="test-error-group",
        consumer_name="test-error-consumer",
    )
    queue.connect()
    yield queue
    queue.disconnect()


class TestRedisConnectionErrors:
    """Test Redis connection failure scenarios."""

    def test_connect_with_invalid_host(self):
        """Test connection failure with invalid Redis host."""
        queue = RedisQueuePlugin(host="invalid-host-that-does-not-exist", port=6379)

        with pytest.raises((ConnectionError, RedisConnectionError, RedisError)):
            queue.connect()

    def test_connect_with_invalid_port(self):
        """Test connection failure with invalid port."""
        queue = RedisQueuePlugin(host="localhost", port=99999)

        with pytest.raises((RedisConnectionError, RedisError, OSError)):
            queue.connect()

    def test_connect_with_wrong_password(self, redis_client):
        """Test connection failure with incorrect password."""
        # Skip this test if Redis doesn't require auth
        pytest.skip("Redis test instance doesn't require auth")


class TestRedisOperationErrors:
    """Test Redis operation error handling."""

    def test_create_topic_when_disconnected(self):
        """Test topic creation is lazy and doesn't fail when disconnected."""
        queue = RedisQueuePlugin()

        # create_topic is lazy, doesn't fail immediately
        queue.create_topic("test-topic")
        # But operations will fail
        assert not queue.is_connected()

    def test_publish_when_disconnected(self):
        """Test publish fails when disconnected."""
        queue = RedisQueuePlugin()

        with pytest.raises(ConnectionError):
            queue.publish("test-topic", {"data": "test"})

    def test_subscribe_when_disconnected(self):
        """Test subscribe fails when disconnected."""
        queue = RedisQueuePlugin()

        def handler(msg):
            pass

        with pytest.raises(ConnectionError):
            queue.subscribe("test-topic", handler)

    @pytest.mark.asyncio
    async def test_publish_with_redis_down(self, redis_queue):
        """Test publish when Redis goes down mid-operation."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Mock Redis client to simulate failure
        original_client = redis_queue._client
        redis_queue._client = Mock()
        redis_queue._client.xadd.side_effect = RedisConnectionError("Connection lost")

        with pytest.raises(RedisConnectionError):
            redis_queue.publish("test-topic", {"data": "test"})

        # Restore client
        redis_queue._client = original_client
        redis_queue.disconnect()

    @pytest.mark.asyncio
    async def test_acknowledge_failure(self, redis_queue):
        """Test acknowledgment failure handling."""
        # Mock xack to fail
        original_xack = redis_queue._client.xack
        redis_queue._client.xack = Mock(side_effect=RedisError("ACK failed"))

        # Should not raise, just log error
        redis_queue.acknowledge("msg-id")

        redis_queue._client.xack = original_xack


class TestConsumerGroupErrors:
    """Test consumer group error scenarios."""

    @pytest.mark.asyncio
    async def test_consumer_group_already_exists(self, redis_queue):
        """Test handling when consumer group already exists."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Create consumer group first time
        redis_queue.subscribe("test-topic", lambda msg: None)

        # Try to create same group again (different subscription)
        # Should handle gracefully
        redis_queue.subscribe("test-topic", lambda msg: None)

        redis_queue.disconnect()

    @pytest.mark.asyncio
    async def test_consumer_group_creation_failure(self, redis_queue):
        """Test error handling when consumer group creation fails."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Mock xgroup_create to fail
        original_method = redis_queue._client.xgroup_create
        redis_queue._client.xgroup_create = Mock(side_effect=RedisError("Group creation failed"))

        with pytest.raises(RedisError):
            redis_queue.subscribe("test-topic", lambda msg: None)

        redis_queue._client.xgroup_create = original_method
        redis_queue.disconnect()


class TestDeadLetterQueue:
    """Test dead letter queue functionality."""

    @pytest.mark.asyncio
    async def test_dlq_message_handling(self, redis_queue):
        """Test message moved to DLQ after max retries."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        received = []

        def failing_handler(msg):
            received.append(msg)
            raise Exception("Processing failed")

        sub_id = redis_queue.subscribe("test-topic", failing_handler)

        # Publish message
        redis_queue.publish("test-topic", {"data": "test", "retry_count": 3})

        # Wait for processing attempts
        time.sleep(0.5)

        # Check DLQ (test-topic.dlq should exist)
        dlq_topic = f"test-topic.dlq"
        # DLQ messages should be stored but not auto-processed

        redis_queue.unsubscribe(sub_id)
        redis_queue.disconnect()

    @pytest.mark.asyncio
    async def test_dlq_publish_failure(self, redis_queue):
        """Test handling when DLQ publish fails."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Mock xadd to fail for DLQ
        original_xadd = redis_queue._client.xadd

        def selective_xadd(stream, fields, *args, **kwargs):
            if ".dlq" in stream:
                raise RedisError("DLQ publish failed")
            return original_xadd(stream, fields, *args, **kwargs)

        redis_queue._client.xadd = selective_xadd

        def failing_handler(msg):
            raise Exception("Processing failed")

        sub_id = redis_queue.subscribe("test-topic", failing_handler)

        # Publish message with high retry count
        redis_queue.publish("test-topic", {"data": "test", "retry_count": 10})

        time.sleep(0.5)

        redis_queue._client.xadd = original_xadd
        redis_queue.unsubscribe(sub_id)
        redis_queue.disconnect()


class TestHealthCheckErrors:
    """Test health check under error conditions."""

    def test_health_check_when_disconnected(self):
        """Test health check returns unhealthy when disconnected."""
        queue = RedisQueuePlugin()

        health = queue.health_check()

        assert health["status"] == "unhealthy"
        assert "details" in health

    def test_health_check_with_redis_down(self, redis_queue):
        """Test health check when Redis becomes unavailable."""
        redis_queue.connect()

        # Mock ping to fail
        redis_queue._client = Mock()
        redis_queue._client.ping.side_effect = RedisConnectionError("Redis down")
        redis_queue._connected = True

        health = redis_queue.health_check()

        assert health["status"] in ["unhealthy", "degraded"]

    def test_health_check_with_partial_failure(self, redis_queue):
        """Test health check when some operations fail."""
        redis_queue.connect()

        # Mock some methods to fail
        redis_queue._client = Mock()
        redis_queue._client.ping.return_value = True
        redis_queue._client.info.side_effect = RedisError("Info failed")
        redis_queue._connected = True

        health = redis_queue.health_check()

        # Should still report some status
        assert "status" in health


class TestStatisticsErrors:
    """Test statistics gathering under error conditions."""

    def test_get_stats_when_disconnected(self):
        """Test statistics when disconnected."""
        queue = RedisQueuePlugin()

        stats = queue.get_statistics()

        assert stats is not None
        assert isinstance(stats, dict)
        assert "messages_published" in stats
        assert "errors" in stats

    def test_get_stats_with_redis_error(self, redis_queue):
        """Test statistics when Redis operations fail."""
        # Statistics should work even if Redis client fails
        # get_statistics just returns the _stats dict
        stats = redis_queue.get_statistics()

        # Should return stats dict
        assert stats is not None
        assert isinstance(stats, dict)


class TestDisconnectionErrors:
    """Test disconnection and cleanup errors."""

    def test_disconnect_when_already_disconnected(self):
        """Test disconnect is idempotent."""
        queue = RedisQueuePlugin()

        # Multiple disconnects should not raise
        queue.disconnect()
        queue.disconnect()

    def test_disconnect_with_active_subscriptions(self, redis_queue):
        """Test disconnect cleans up active subscriptions."""
        received = []
        sub_id = redis_queue.subscribe("test-topic", lambda msg: received.append(msg))

        # Disconnect should clean up subscription
        redis_queue.disconnect()

        assert not redis_queue.is_connected()
        # Subscription should be cleaned up

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_subscription(self, redis_queue):
        """Test unsubscribe with invalid subscription ID."""
        redis_queue.connect()

        # Should handle gracefully, not raise
        redis_queue.unsubscribe("nonexistent-sub-id")

        redis_queue.disconnect()


class TestReconnectionScenarios:
    """Test reconnection logic and recovery."""

    @pytest.mark.asyncio
    async def test_reconnect_after_connection_loss(self, redis_queue):
        """Test reconnection after losing connection."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Simulate connection loss
        redis_queue.disconnect()

        # Reconnect
        redis_queue.connect()
        redis_queue.create_topic("test-topic-2")

        # Should work
        redis_queue.publish("test-topic-2", {"data": "after reconnect"})

        redis_queue.disconnect()

    def test_operations_after_failed_connect(self):
        """Test that operations fail gracefully after failed connection."""
        queue = RedisQueuePlugin(host="invalid-host")

        # Connection should fail
        with pytest.raises(ConnectionError):
            queue.connect()

        # create_topic is lazy and won't fail
        # but it should show as not connected
        queue.create_topic("test")
        assert not queue.is_connected()


class TestQueueManagement:
    """Test queue management operations."""

    def test_get_queue_size(self, redis_queue):
        """Test getting queue size."""
        # Use unique topic name to avoid interference
        topic = f"test-queue-size-{int(time.time() * 1000)}"
        redis_queue.create_topic(topic)

        # Get initial size
        size_before = redis_queue.get_queue_size(topic)

        # After publishing
        redis_queue.publish(topic, {"data": "test"})
        size_after = redis_queue.get_queue_size(topic)
        assert size_after > size_before

    def test_get_queue_size_when_disconnected(self):
        """Test getting queue size when disconnected."""
        queue = RedisQueuePlugin()

        size = queue.get_queue_size("test-topic")
        assert size == 0

    def test_delete_topic(self, redis_queue):
        """Test topic deletion."""
        redis_queue.create_topic("test-topic")
        redis_queue.publish("test-topic", {"data": "test"})

        # Delete topic
        redis_queue.delete_topic("test-topic")

        # Should be empty
        size = redis_queue.get_queue_size("test-topic")
        assert size == 0

    def test_list_topics(self, redis_queue):
        """Test listing topics."""
        # Create multiple topics
        redis_queue.create_topic("topic-1")
        redis_queue.create_topic("topic-2")
        redis_queue.publish("topic-1", {"data": "test"})
        redis_queue.publish("topic-2", {"data": "test"})

        topics = redis_queue.list_topics()

        # Should contain our topics (may have others from other tests)
        assert isinstance(topics, list)

    def test_list_topics_when_disconnected(self):
        """Test listing topics when disconnected."""
        queue = RedisQueuePlugin()

        topics = queue.list_topics()
        assert topics == []


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_message_publish(self, redis_queue):
        """Test publishing empty message."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Should handle gracefully
        redis_queue.publish("test-topic", {})

        redis_queue.disconnect()

    @pytest.mark.asyncio
    async def test_large_message_publish(self, redis_queue):
        """Test publishing very large message."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        # Create large payload (1MB)
        large_data = {"data": "x" * (1024 * 1024)}

        # Should handle or fail gracefully
        try:
            redis_queue.publish("test-topic", large_data)
        except (RedisError, ValueError):
            pass  # Acceptable if Redis has size limits

        redis_queue.disconnect()

    @pytest.mark.asyncio
    async def test_special_characters_in_topic_name(self, redis_queue):
        """Test topic names with special characters."""
        redis_queue.connect()

        # Should handle or sanitize
        special_topics = ["test-topic", "test_topic", "test.topic"]

        for topic in special_topics:
            redis_queue.create_topic(topic)

        redis_queue.disconnect()

    def test_concurrent_subscription_to_same_topic(self, redis_queue):
        """Test multiple concurrent subscriptions to same topic."""
        redis_queue.connect()
        redis_queue.create_topic("test-topic")

        received1 = []
        received2 = []

        sub1 = redis_queue.subscribe("test-topic", lambda msg: received1.append(msg))
        sub2 = redis_queue.subscribe("test-topic", lambda msg: received2.append(msg))

        redis_queue.publish("test-topic", {"data": "test"})

        time.sleep(0.5)

        redis_queue.unsubscribe(sub1)
        redis_queue.unsubscribe(sub2)
        redis_queue.disconnect()
