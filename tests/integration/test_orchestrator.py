"""
Integration tests for ProcessingOrchestrator.

Tests the full pipeline flow including:
- Orchestrator lifecycle (start/stop)
- Event consumption from queue
- Health checks
- Statistics tracking
"""

import time

import pytest

from core.models.events import (
    EventMetadata,
    EventStatus,
    EventType,
    RawListingEvent,
    Topics,
)
from core.pipeline.orchestrator import ProcessingOrchestrator
from core.plugin_manager import PluginManager
from core.queue.in_memory_queue import InMemoryQueuePlugin


@pytest.fixture
def queue():
    """Create an in-memory queue for testing"""
    q = InMemoryQueuePlugin()
    q.connect()
    q.create_topic(Topics.RAW_LISTINGS)
    q.create_topic(Topics.PROCESSED_LISTINGS)
    q.create_topic(Topics.PROCESSING_FAILED)
    yield q
    q.disconnect()


@pytest.fixture
def plugin_manager():
    """Create a plugin manager for testing"""
    return PluginManager()


@pytest.fixture
def orchestrator(plugin_manager, queue):
    """Create an orchestrator instance"""
    orch = ProcessingOrchestrator(
        plugin_manager=plugin_manager, queue=queue, max_retries=3
    )
    yield orch
    if orch.is_running():
        orch.stop()


class TestOrchestratorBasics:
    """Test basic orchestrator functionality"""

    def test_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator is not None
        assert not orchestrator.is_running()
        assert orchestrator._stats["events_processed"] == 0
        assert orchestrator._stats["events_failed"] == 0

    def test_start_stop(self, orchestrator):
        """Test starting and stopping orchestrator"""
        assert not orchestrator.is_running()

        orchestrator.start()
        assert orchestrator.is_running()
        assert orchestrator._subscription_id is not None

        orchestrator.stop()
        assert not orchestrator.is_running()
        assert orchestrator._subscription_id is None

    def test_double_start_warning(self, orchestrator, caplog):
        """Test starting already running orchestrator logs warning"""
        orchestrator.start()
        orchestrator.start()

        assert "already running" in caplog.text

    def test_stop_when_not_running(self, orchestrator):
        """Test stopping orchestrator that is not running"""
        assert not orchestrator.is_running()
        orchestrator.stop()  # Should not raise error
        assert not orchestrator.is_running()


class TestHealthCheck:
    """Test health check functionality"""

    def test_health_check_when_stopped(self, orchestrator):
        """Test health check when orchestrator is stopped"""
        health = orchestrator.health_check()

        assert health["status"] == "unhealthy"
        assert not health["running"]
        assert "queue_health" in health
        assert "statistics" in health

    def test_health_check_when_running(self, orchestrator):
        """Test health check when orchestrator is running"""
        orchestrator.start()
        health = orchestrator.health_check()

        assert health["status"] == "healthy"
        assert health["running"]
        assert health["queue_health"]["status"] == "healthy"
        assert "statistics" in health


class TestEventProcessing:
    """Test event processing functionality"""

    def test_process_event_without_plugins(self, orchestrator, queue):
        """Test processing when no plugins are available"""
        orchestrator.start()

        # Monitor processed events
        processed = []

        def capture_processed(msg):
            processed.append(msg)

        queue.subscribe(Topics.PROCESSED_LISTINGS, capture_processed)

        # Create and publish event
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
            ),
            raw_data={"listing_id": "test-001", "price": 100000},
        )

        queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        # Wait for processing
        time.sleep(0.3)

        # Check results
        assert len(processed) >= 1
        latest = processed[-1]
        assert latest["listing_data"]["listing_id"] == "test-001"
        assert latest["listing_data"]["price"] == 100000
        assert latest["plugins_applied"] == []
        assert latest["metadata"]["status"] == EventStatus.COMPLETED

    def test_event_metadata_propagation(self, orchestrator, queue):
        """Test that event metadata is correctly propagated"""
        orchestrator.start()

        # Monitor processed events
        processed = []
        queue.subscribe(Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg))

        # Create event with full metadata
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="cian-source",
                source_platform="cian.ru",
                trace_id="trace-123",
                request_id="req-456",
            ),
            raw_data={"listing_id": "test-metadata", "title": "Test Listing"},
        )

        queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        # Wait for processing
        time.sleep(0.3)

        # Verify metadata propagation
        assert len(processed) >= 1
        latest = processed[-1]
        assert latest["metadata"]["trace_id"] == "trace-123"
        assert latest["metadata"]["request_id"] == "req-456"
        assert latest["metadata"]["parent_event_id"] == event.metadata.event_id
        assert latest["metadata"]["source_platform"] == "cian.ru"
        assert latest["metadata"]["event_type"] == EventType.PROCESSED_LISTING


class TestStatistics:
    """Test statistics collection"""

    def test_initial_statistics(self, orchestrator):
        """Test initial statistics are zeroed"""
        stats = orchestrator.get_statistics()

        assert stats["events_processed"] == 0
        assert stats["events_failed"] == 0
        assert stats["total_processing_time_ms"] == 0.0
        assert stats["avg_processing_time_ms"] == 0.0

    def test_statistics_after_processing(self, orchestrator, queue):
        """Test statistics are updated after processing events"""
        orchestrator.start()

        # Process multiple events
        for i in range(3):
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                ),
                raw_data={"listing_id": f"test-{i:03d}", "price": 100000 + (i * 10000)},
            )
            queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        # Wait for processing
        time.sleep(0.5)

        # Check statistics
        stats = orchestrator.get_statistics()
        assert stats["events_processed"] == 3
        assert stats["total_processing_time_ms"] > 0
        assert stats["avg_processing_time_ms"] > 0
        assert stats["avg_processing_time_ms"] == (
            stats["total_processing_time_ms"] / stats["events_processed"]
        )


class TestQueueIntegration:
    """Test integration with queue implementations"""

    def test_orchestrator_with_in_memory_queue(self, plugin_manager):
        """Test orchestrator works with in-memory queue"""
        queue = InMemoryQueuePlugin()
        queue.connect()
        queue.create_topic(Topics.RAW_LISTINGS)
        queue.create_topic(Topics.PROCESSED_LISTINGS)
        queue.create_topic(Topics.PROCESSING_FAILED)

        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue
        )

        try:
            orchestrator.start()
            assert orchestrator.is_running()

            health = orchestrator.health_check()
            assert health["status"] == "healthy"
            assert health["queue_health"]["status"] == "healthy"
        finally:
            orchestrator.stop()
            queue.disconnect()

    def test_multiple_events_in_sequence(self, orchestrator, queue):
        """Test processing multiple events in sequence"""
        orchestrator.start()

        # Monitor processed events
        processed_count = [0]

        def count_processed(msg):
            processed_count[0] += 1

        queue.subscribe(Topics.PROCESSED_LISTINGS, count_processed)

        # Publish multiple events
        event_count = 5
        for i in range(event_count):
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                ),
                raw_data={"listing_id": f"test-seq-{i:03d}"},
            )
            queue.publish(Topics.RAW_LISTINGS, event.to_dict())

        # Wait for all processing to complete
        time.sleep(0.8)

        # Verify all events were processed
        assert processed_count[0] == event_count

        # Verify statistics
        stats = orchestrator.get_statistics()
        assert stats["events_processed"] == event_count
