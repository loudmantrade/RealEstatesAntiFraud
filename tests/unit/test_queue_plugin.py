"""Tests for queue plugin implementations"""

import time
from threading import Event
from typing import Any, Dict, List

import pytest

from core.queue import InMemoryQueuePlugin


class TestInMemoryQueuePlugin:
    """Tests for InMemoryQueuePlugin"""

    @pytest.fixture
    def queue(self):
        """Create queue instance"""
        plugin = InMemoryQueuePlugin()
        plugin.connect()
        yield plugin
        plugin.disconnect()

    def test_connect_disconnect(self):
        """Test connection lifecycle"""
        plugin = InMemoryQueuePlugin()

        assert not plugin.is_connected()

        plugin.connect()
        assert plugin.is_connected()

        plugin.disconnect()
        assert not plugin.is_connected()

    def test_create_topic(self, queue):
        """Test topic creation"""
        topic = "test.topic"

        queue.create_topic(topic)

        topics = queue.list_topics()
        assert topic in topics

    def test_publish_message(self, queue):
        """Test message publishing"""
        topic = "test.publish"
        queue.create_topic(topic)

        message = {"id": "123", "data": "test"}

        message_id = queue.publish(topic, message)
        assert message_id is not None

        # Check queue size
        size = queue.get_queue_size(topic)
        assert size == 1

    def test_subscribe_receive(self, queue):
        """Test subscription and message receiving"""
        topic = "test.subscribe"
        queue.create_topic(topic)

        received_messages: List[Dict[str, Any]] = []
        received_event = Event()

        def callback(message: Dict[str, Any]) -> None:
            received_messages.append(message)
            received_event.set()

        # Subscribe
        sub_id = queue.subscribe(topic, callback)
        assert sub_id is not None

        # Publish message
        test_message = {"id": "456", "data": "hello"}
        queue.publish(topic, test_message)

        # Wait for message
        received = received_event.wait(timeout=2.0)
        assert received is True
        assert len(received_messages) == 1
        assert received_messages[0] == test_message

        # Cleanup
        queue.unsubscribe(sub_id)

    def test_multiple_subscriptions(self, queue):
        """Test multiple subscribers on same topic"""
        topic = "test.multi"
        queue.create_topic(topic)

        received1: List[Dict[str, Any]] = []
        received2: List[Dict[str, Any]] = []

        def callback1(message: Dict[str, Any]) -> None:
            received1.append(message)

        def callback2(message: Dict[str, Any]) -> None:
            received2.append(message)

        # Subscribe with both callbacks
        sub_id1 = queue.subscribe(topic, callback1)
        sub_id2 = queue.subscribe(topic, callback2)

        # Give workers time to start
        time.sleep(0.1)

        # Publish message
        test_message = {"id": "789", "data": "broadcast"}
        queue.publish(topic, test_message)

        # Wait for processing
        time.sleep(0.5)

        # Only one subscriber gets the message (round-robin)
        total_received = len(received1) + len(received2)
        assert total_received >= 1

        # Cleanup
        queue.unsubscribe(sub_id1)
        queue.unsubscribe(sub_id2)

    def test_unsubscribe(self, queue):
        """Test unsubscribe stops receiving messages"""
        topic = "test.unsub"
        queue.create_topic(topic)

        received: List[Dict[str, Any]] = []

        def callback(message: Dict[str, Any]) -> None:
            received.append(message)

        # Subscribe and wait for worker to start
        sub_id = queue.subscribe(topic, callback)
        time.sleep(0.2)

        # Publish and wait
        queue.publish(topic, {"id": "1"})
        time.sleep(0.3)

        # Unsubscribe
        queue.unsubscribe(sub_id)
        time.sleep(0.1)

        # Publish again
        queue.publish(topic, {"id": "2"})
        time.sleep(0.2)

        # Should only have received first message
        assert len(received) == 1
        assert received[0]["id"] == "1"

    def test_acknowledge_message(self, queue):
        """Test message acknowledgment"""
        topic = "test.ack"
        queue.create_topic(topic)

        received: List[str] = []

        def callback(message: Dict[str, Any]) -> None:
            msg_id = message.get("_message_id")
            received.append(msg_id)
            # Auto-acknowledged by queue implementation

        sub_id = queue.subscribe(topic, callback)
        time.sleep(0.2)  # Wait for worker to start

        queue.publish(topic, {"data": "test"})
        time.sleep(0.3)  # Wait for processing

        assert len(received) == 1

        queue.unsubscribe(sub_id)

    def test_reject_message(self, queue):
        """Test message rejection"""
        topic = "test.reject"
        queue.create_topic(topic)

        message = {"data": "reject_me"}
        msg_id = queue.publish(topic, message)

        # Reject (would go to DLQ in real implementation)
        # For in-memory queue, just test the method exists
        queue.reject(msg_id, requeue=False)

        # Method doesn't return value, just check it doesn't raise

    def test_purge_queue(self, queue):
        """Test queue purging"""
        topic = "test.purge"
        queue.create_topic(topic)

        # Publish multiple messages
        for i in range(5):
            queue.publish(topic, {"id": str(i)})

        # Check size
        assert queue.get_queue_size(topic) == 5

        # Purge
        purged_count = queue.purge_queue(topic)
        assert purged_count == 5

        # Should be empty
        assert queue.get_queue_size(topic) == 0

    def test_delete_topic(self, queue):
        """Test topic deletion"""
        topic = "test.delete"
        queue.create_topic(topic)

        assert topic in queue.list_topics()

        queue.delete_topic(topic)

        assert topic not in queue.list_topics()

    def test_statistics(self, queue):
        """Test statistics tracking"""
        topic = "test.stats"
        queue.create_topic(topic)

        # Publish messages
        for i in range(3):
            queue.publish(topic, {"id": str(i)})

        stats = queue.get_statistics()

        assert "messages_published" in stats
        assert stats["messages_published"] >= 3
        assert "messages_consumed" in stats

    def test_health_check(self, queue):
        """Test health check"""
        health = queue.health_check()

        assert "status" in health
        assert health["status"] == "healthy"
        assert "details" in health
        assert health["details"]["connected"] is True

    def test_get_queue_size_nonexistent_topic(self, queue):
        """Test getting size of non-existent topic"""
        size = queue.get_queue_size("nonexistent.topic")
        assert size == 0

    def test_publish_to_nonexistent_topic(self, queue):
        """Test publishing to non-existent topic creates it"""
        topic = "test.autocreate"

        # Should auto-create topic
        message_id = queue.publish(topic, {"data": "test"})
        assert message_id is not None

        # Topic should exist
        assert topic in queue.list_topics()

    def test_concurrent_publish(self, queue):
        """Test concurrent publishing from multiple threads"""
        import threading

        topic = "test.concurrent"
        queue.create_topic(topic)

        num_threads = 5
        messages_per_thread = 10

        def publish_messages():
            for i in range(messages_per_thread):
                queue.publish(topic, {"thread_id": threading.get_ident(), "msg": i})

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=publish_messages)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Check all messages were published
        size = queue.get_queue_size(topic)
        assert size == num_threads * messages_per_thread

    def test_message_ordering(self, queue):
        """Test FIFO ordering of messages"""
        topic = "test.ordering"
        queue.create_topic(topic)

        # Publish ordered messages
        for i in range(10):
            queue.publish(topic, {"seq": i})

        received: List[int] = []
        event = Event()

        def callback(message: Dict[str, Any]) -> None:
            received.append(message["seq"])
            if len(received) == 10:
                event.set()

        sub_id = queue.subscribe(topic, callback)

        # Wait for all messages
        event.wait(timeout=2.0)

        # Should be in order
        assert received == list(range(10))

        queue.unsubscribe(sub_id)

    def test_error_in_callback(self, queue):
        """Test that errors in callbacks are handled gracefully"""
        topic = "test.error"
        queue.create_topic(topic)

        def failing_callback(message: Dict[str, Any]) -> None:
            raise ValueError("Test error")

        sub_id = queue.subscribe(topic, failing_callback)

        # Should not crash
        queue.publish(topic, {"data": "test"})
        time.sleep(0.2)

        # Queue should still be operational
        health = queue.health_check()
        assert health["status"] == "healthy"

        queue.unsubscribe(sub_id)
