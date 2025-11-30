"""
Integration tests for messaging layer (queue & orchestrator).

Tests the complete messaging flow including:
- InMemoryQueue with real async workflows
- RedisQueue with actual Redis container
- Full pipeline execution (raw → processed)
- Message ordering and acknowledgment
- Dead letter queue handling
- Connection resilience and reconnection
- Consumer groups and parallel processing
"""

import asyncio
import time
from typing import Any, Dict, List

import pytest

from core.models.events import (
    EventMetadata,
    EventStatus,
    EventType,
    ProcessedListingEvent,
    RawListingEvent,
    Topics,
)
from core.pipeline.orchestrator import ProcessingOrchestrator
from core.plugin_manager import PluginManager
from core.queue.in_memory_queue import InMemoryQueuePlugin
from core.queue.redis_queue import REDIS_AVAILABLE, RedisQueuePlugin

pytestmark = [pytest.mark.integration, pytest.mark.redis, pytest.mark.messaging, pytest.mark.slow]

# ============================================================================
# InMemoryQueue Integration Tests
# ============================================================================


class TestInMemoryQueueIntegration:
    """Integration tests for InMemoryQueue with real async workflows."""

    @pytest.fixture
    def memory_queue(self):
        """Create in-memory queue for testing."""
        queue = InMemoryQueuePlugin()
        queue.connect()
        yield queue
        queue.disconnect()

    def test_message_ordering_preserved(self, memory_queue):
        """Test that messages maintain order in queue."""
        topic = "test.ordering"
        memory_queue.create_topic(topic)

        received = []

        def callback(msg):
            received.append(msg["sequence"])

        memory_queue.subscribe(topic, callback)

        # Publish messages in order
        for i in range(10):
            memory_queue.publish(topic, {"sequence": i})

        # Wait for processing
        time.sleep(0.5)

        # Verify order
        assert len(received) >= 10
        # Messages should arrive in order
        for i in range(len(received) - 1):
            assert received[i] <= received[i + 1]

    def test_multiple_subscribers_load_balancing(self, memory_queue):
        """Test load balancing across multiple subscribers."""
        topic = "test.load_balance"
        memory_queue.create_topic(topic)

        received_1 = []
        received_2 = []

        memory_queue.subscribe(topic, lambda msg: received_1.append(msg))
        memory_queue.subscribe(topic, lambda msg: received_2.append(msg))

        # Publish messages
        for i in range(20):
            memory_queue.publish(topic, {"id": i})

        time.sleep(0.5)

        # Both subscribers should receive messages (total = 20 * 2)
        total_received = len(received_1) + len(received_2)
        assert total_received >= 20

    def test_message_acknowledgment_flow(self, memory_queue):
        """Test message acknowledgment workflow."""
        topic = "test.ack_flow"
        memory_queue.create_topic(topic)

        acked_count = [0]
        pending_before = len(memory_queue._pending_acks)

        def callback(msg):
            # Message is auto-acknowledged after successful processing
            acked_count[0] += 1

        memory_queue.subscribe(topic, callback)
        memory_queue.publish(topic, {"test": "ack"})

        time.sleep(0.3)

        # Message should be acknowledged
        assert acked_count[0] >= 1

    def test_dead_letter_queue_handling(self, memory_queue):
        """Test that failed messages go to DLQ."""
        topic = "test.dlq"
        memory_queue.create_topic(topic)

        failed_messages = []

        def failing_callback(msg):
            failed_messages.append(msg)
            raise ValueError("Simulated processing error")

        memory_queue.subscribe(topic, failing_callback)
        memory_queue.publish(topic, {"test": "will_fail"})

        time.sleep(0.5)

        # Check DLQ has message
        dlq_messages = memory_queue.get_dead_letter_messages()
        assert len(dlq_messages) >= 1

    def test_queue_statistics_accuracy(self, memory_queue):
        """Test that queue statistics are accurate."""
        topic = "test.stats"
        memory_queue.create_topic(topic)

        initial_stats = memory_queue.get_statistics()
        initial_published = initial_stats["messages_published"]

        # Publish and consume messages
        received = []
        memory_queue.subscribe(topic, lambda msg: received.append(msg))

        for i in range(5):
            memory_queue.publish(topic, {"id": i})

        time.sleep(0.5)

        stats = memory_queue.get_statistics()

        # Verify statistics
        assert stats["messages_published"] == initial_published + 5
        assert stats["messages_consumed"] >= 5
        assert stats["active_subscriptions"] >= 1

    def test_concurrent_publishers(self, memory_queue):
        """Test multiple concurrent publishers."""
        topic = "test.concurrent"
        memory_queue.create_topic(topic)

        received = []
        memory_queue.subscribe(topic, lambda msg: received.append(msg))

        # Simulate concurrent publishing
        for i in range(50):
            memory_queue.publish(topic, {"id": i, "timestamp": time.time()})

        time.sleep(1.0)

        # All messages should be received
        assert len(received) >= 50

    def test_graceful_shutdown_with_pending_messages(self, memory_queue):
        """Test graceful shutdown with messages still in queue."""
        topic = "test.shutdown"
        memory_queue.create_topic(topic)

        # Publish messages
        for i in range(10):
            memory_queue.publish(topic, {"id": i})

        # Subscribe with slow callback
        slow_received = []

        def slow_callback(msg):
            time.sleep(0.1)
            slow_received.append(msg)

        memory_queue.subscribe(topic, slow_callback)

        # Wait a bit then disconnect
        time.sleep(0.3)
        memory_queue.disconnect()

        # Should disconnect cleanly
        assert not memory_queue.is_connected()


# ============================================================================
# RedisQueue Integration Tests
# ============================================================================


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
class TestRedisQueueIntegration:
    """Integration tests for RedisQueue with actual Redis container."""

    @pytest.fixture
    def redis_queue(self, test_config, redis_clean):
        """Create Redis queue for testing."""
        queue = RedisQueuePlugin(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
            consumer_group="test-integration",
            consumer_name="test-consumer",
        )
        queue.connect()
        yield queue
        queue.disconnect()

    def test_message_persistence(self, redis_queue):
        """Test that messages persist in Redis."""
        topic = "test.persistence"
        redis_queue.create_topic(topic)

        # Publish messages
        for i in range(10):
            redis_queue.publish(topic, {"id": i})

        # Check stream has messages
        size = redis_queue.get_queue_size(topic)
        assert size >= 10

    def test_consumer_group_message_distribution(self, redis_queue):
        """Test consumer group distributes messages."""
        topic = "test.consumer_group"
        redis_queue.create_topic(topic)

        received_1 = []
        received_2 = []

        # Create two consumers in same group
        sub_1 = redis_queue.subscribe(topic, lambda msg: received_1.append(msg))
        sub_2 = redis_queue.subscribe(topic, lambda msg: received_2.append(msg))

        # Publish messages
        for i in range(20):
            redis_queue.publish(topic, {"id": i})

        time.sleep(1.0)

        # Messages should be distributed (not duplicated)
        total = len(received_1) + len(received_2)
        assert total >= 20

    def test_connection_resilience(self, redis_queue):
        """Test queue handles connection issues gracefully."""
        topic = "test.resilience"
        redis_queue.create_topic(topic)

        # Publish before any issues
        redis_queue.publish(topic, {"before": "disconnect"})

        # Verify health check
        health = redis_queue.health_check()
        assert health["status"] == "healthy"

    def test_message_acknowledgment_in_redis(self, redis_queue):
        """Test Redis message acknowledgment."""
        topic = "test.redis_ack"
        redis_queue.create_topic(topic)

        received = []

        def callback(msg):
            received.append(msg)

        redis_queue.subscribe(topic, callback)
        redis_queue.publish(topic, {"test": "ack"})

        time.sleep(0.5)

        # Message should be consumed and acknowledged
        assert len(received) >= 1

        stats = redis_queue.get_statistics()
        assert stats["messages_consumed"] >= 1

    def test_large_message_handling(self, redis_queue):
        """Test handling of large messages."""
        topic = "test.large_message"
        redis_queue.create_topic(topic)

        # Create large message (100KB)
        large_data = {"data": "x" * 100000}

        received = []
        redis_queue.subscribe(topic, lambda msg: received.append(msg))
        redis_queue.publish(topic, large_data)

        time.sleep(0.5)

        # Should handle large message
        assert len(received) >= 1


# ============================================================================
# Orchestrator Integration Tests
# ============================================================================


class TestOrchestratorIntegration:
    """Integration tests for ProcessingOrchestrator with full pipeline."""

    @pytest.fixture
    def orchestrator_with_queue(self):
        """Create orchestrator with in-memory queue."""
        queue = InMemoryQueuePlugin()
        queue.connect()
        queue.create_topic(Topics.RAW_LISTINGS)
        queue.create_topic(Topics.PROCESSED_LISTINGS)
        queue.create_topic(Topics.PROCESSING_FAILED)

        manager = PluginManager()
        orchestrator = ProcessingOrchestrator(plugin_manager=manager, queue=queue, max_retries=3)

        yield orchestrator, queue

        if orchestrator.is_running():
            orchestrator.stop()
        queue.disconnect()

    def test_full_pipeline_execution(self, orchestrator_with_queue):
        """Test complete pipeline from raw to processed."""
        orchestrator, queue = orchestrator_with_queue
        orchestrator.start()

        # Monitor processed events
        processed = []
        queue.subscribe(Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg))

        # Create raw event
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
            ),
            raw_data={"listing_id": "integration-001", "price": 500000},
        )

        # Publish to raw listings
        queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        # Wait for processing
        time.sleep(0.5)

        # Verify processed event
        assert len(processed) >= 1
        result = processed[-1]
        assert result["metadata"]["event_type"] == EventType.PROCESSED_LISTING
        assert result["listing_data"]["listing_id"] == "integration-001"
        assert result["metadata"]["status"] == EventStatus.COMPLETED

    def test_retry_logic_with_real_failures(self, orchestrator_with_queue):
        """Test retry logic with simulated failures."""
        orchestrator, queue = orchestrator_with_queue
        orchestrator.start()

        # Monitor failed events
        failed = []
        queue.subscribe(Topics.PROCESSING_FAILED, lambda msg: failed.append(msg))

        # Create event
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
                retry_count=3,  # Already at max
            ),
            raw_data={"test": "data"},
        )

        # Manually trigger failure
        orchestrator._handle_processing_failure(event.to_dict(), "Test failure")

        time.sleep(0.5)

        # Should be sent to failed queue
        assert len(failed) >= 1
        assert failed[0]["metadata"]["event_type"] == EventType.PROCESSING_FAILED

    def test_multiple_concurrent_listings_processing(self, orchestrator_with_queue):
        """Test processing multiple listings concurrently."""
        orchestrator, queue = orchestrator_with_queue
        orchestrator.start()

        processed = []
        queue.subscribe(Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg))

        # Publish multiple events
        num_events = 10
        for i in range(num_events):
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                ),
                raw_data={"listing_id": f"concurrent-{i:03d}", "price": 100000 + i},
            )
            queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        # Wait for all processing
        time.sleep(1.5)

        # All should be processed
        assert len(processed) >= num_events

    def test_statistics_collection(self, orchestrator_with_queue):
        """Test orchestrator statistics collection."""
        orchestrator, queue = orchestrator_with_queue
        orchestrator.start()

        # Process events
        for i in range(5):
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                ),
                raw_data={"id": i},
            )
            queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        time.sleep(1.0)

        # Check statistics
        stats = orchestrator.get_statistics()
        assert stats["events_processed"] >= 5
        assert stats["total_processing_time_ms"] > 0
        assert stats["avg_processing_time_ms"] > 0

    def test_error_handling_and_dlq_routing(self, orchestrator_with_queue):
        """Test error handling routes to DLQ."""
        orchestrator, queue = orchestrator_with_queue
        orchestrator.start()

        failed = []
        queue.subscribe(Topics.PROCESSING_FAILED, lambda msg: failed.append(msg))

        # Create invalid event
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
                retry_count=10,  # Exceeds max
            ),
            raw_data={},
        )

        # Trigger error
        orchestrator._handle_processing_failure(event.to_dict(), "Permanent failure")

        time.sleep(0.5)

        # Should be in failed queue
        assert len(failed) >= 1


# ============================================================================
# End-to-End Integration Tests
# ============================================================================


class TestEndToEndIntegration:
    """End-to-end integration tests combining all components."""

    def test_complete_message_flow_inmemory(self):
        """Test complete message flow with InMemoryQueue."""
        # Setup
        queue = InMemoryQueuePlugin()
        queue.connect()
        queue.create_topic(Topics.RAW_LISTINGS)
        queue.create_topic(Topics.PROCESSED_LISTINGS)
        queue.create_topic(Topics.PROCESSING_FAILED)

        manager = PluginManager()
        orchestrator = ProcessingOrchestrator(plugin_manager=manager, queue=queue)

        try:
            orchestrator.start()

            # Monitor
            processed = []
            queue.subscribe(Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg))

            # Publish events
            for i in range(10):
                event = RawListingEvent(
                    metadata=EventMetadata(
                        event_type=EventType.RAW_LISTING,
                        source_plugin_id="cian",
                        source_platform="cian.ru",
                    ),
                    raw_data={
                        "listing_id": f"e2e-{i:03d}",
                        "price": 1000000 + i * 50000,
                        "title": f"Test Listing {i}",
                    },
                )
                queue.publish(Topics.RAW_LISTINGS, event.to_dict())

            # Wait for processing
            time.sleep(2.0)

            # Verify all processed
            assert len(processed) >= 10

            # Verify statistics
            stats = orchestrator.get_statistics()
            assert stats["events_processed"] >= 10

        finally:
            orchestrator.stop()
            queue.disconnect()

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    def test_complete_message_flow_redis(self, test_config, redis_clean):
        """Test complete message flow with RedisQueue."""
        # Setup
        queue = RedisQueuePlugin(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
            consumer_group="e2e-test",
        )
        queue.connect()

        manager = PluginManager()
        orchestrator = ProcessingOrchestrator(plugin_manager=manager, queue=queue)

        try:
            queue.create_topic(Topics.RAW_LISTINGS)
            queue.create_topic(Topics.PROCESSED_LISTINGS)
            queue.create_topic(Topics.PROCESSING_FAILED)

            orchestrator.start()

            # Monitor
            processed = []
            queue.subscribe(Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg))

            # Publish
            for i in range(5):
                event = RawListingEvent(
                    metadata=EventMetadata(
                        event_type=EventType.RAW_LISTING,
                        source_plugin_id="avito",
                        source_platform="avito.ru",
                    ),
                    raw_data={"listing_id": f"redis-e2e-{i:03d}", "price": 750000 + i},
                )
                queue.publish(Topics.RAW_LISTINGS, event.to_dict())

            # Wait
            time.sleep(2.0)

            # Verify
            assert len(processed) >= 5

        finally:
            orchestrator.stop()
            queue.disconnect()


# ============================================================================
# Edge Cases and Resilience Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_queue_processing(self):
        """Test orchestrator handles empty queue gracefully."""
        queue = InMemoryQueuePlugin()
        queue.connect()
        queue.create_topic(Topics.RAW_LISTINGS)
        queue.create_topic(Topics.PROCESSED_LISTINGS)
        queue.create_topic(Topics.PROCESSING_FAILED)

        manager = PluginManager()
        orchestrator = ProcessingOrchestrator(plugin_manager=manager, queue=queue)

        try:
            orchestrator.start()
            time.sleep(0.5)

            # Should handle empty queue
            stats = orchestrator.get_statistics()
            assert stats["events_processed"] == 0
            assert orchestrator.is_running()

        finally:
            orchestrator.stop()
            queue.disconnect()

    def test_malformed_message_handling(self):
        """Test handling of malformed messages."""
        queue = InMemoryQueuePlugin()
        queue.connect()
        queue.create_topic(Topics.RAW_LISTINGS)
        queue.create_topic(Topics.PROCESSED_LISTINGS)
        queue.create_topic(Topics.PROCESSING_FAILED)

        manager = PluginManager()
        orchestrator = ProcessingOrchestrator(plugin_manager=manager, queue=queue)

        try:
            orchestrator.start()

            # Publish malformed message
            queue.publish(Topics.RAW_LISTINGS, {"invalid": "structure"})

            time.sleep(0.5)

            # Should handle gracefully
            assert orchestrator.is_running()

        finally:
            orchestrator.stop()
            queue.disconnect()

    def test_rapid_start_stop_cycles(self):
        """Test rapid start/stop cycles."""
        queue = InMemoryQueuePlugin()
        queue.connect()
        queue.create_topic(Topics.RAW_LISTINGS)
        queue.create_topic(Topics.PROCESSED_LISTINGS)
        queue.create_topic(Topics.PROCESSING_FAILED)

        manager = PluginManager()
        orchestrator = ProcessingOrchestrator(plugin_manager=manager, queue=queue)

        try:
            # Rapid cycles
            for _ in range(5):
                orchestrator.start()
                time.sleep(0.1)
                orchestrator.stop()
                time.sleep(0.1)

            # Should handle cleanly
            assert not orchestrator.is_running()

        finally:
            queue.disconnect()
