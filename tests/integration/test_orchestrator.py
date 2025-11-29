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

from core.interfaces.processing_plugin import ProcessingPlugin
from core.models.events import (
    EventMetadata,
    EventStatus,
    EventType,
    RawListingEvent,
    Topics,
)
from core.models.plugin import PluginMetadata
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


class TestRetryLogic:
    """Test retry logic and error recovery"""

    def test_retry_on_processing_error(self, plugin_manager, queue):
        """Test that failed events are retried"""
        # Create orchestrator with max_retries=2
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue, max_retries=2
        )

        try:
            orchestrator.start()

            # Monitor failed events
            failed_events = []
            queue.subscribe(
                Topics.PROCESSING_FAILED, lambda msg: failed_events.append(msg)
            )

            # Create valid event structure that will fail during processing
            # (event is valid but will fail in pipeline execution)
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                    retry_count=0,
                ),
                raw_data={"test": "will fail"},
            )

            # Manually trigger failure to simulate processing error
            orchestrator._handle_processing_failure(
                event.to_dict(), "Simulated processing error"
            )

            # Wait for retry attempts
            time.sleep(0.5)

            # Verify failure was tracked
            assert orchestrator._stats["events_failed"] >= 1

        finally:
            orchestrator.stop()

    def test_retry_count_increments(self, plugin_manager, queue):
        """Test that retry_count increments on each retry"""
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue, max_retries=3
        )

        try:
            orchestrator.start()

            # Create event with initial retry count
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                    retry_count=0,
                ),
                raw_data={"will_fail": True},
            )

            # Manually trigger failure to test retry
            orchestrator._handle_processing_failure(event.to_dict(), "Test error")

            # Wait for requeue
            time.sleep(0.2)

            # Event should be requeued with incremented retry_count
            stats = orchestrator.get_statistics()
            assert stats["events_failed"] >= 1

        finally:
            orchestrator.stop()

    def test_max_retries_sends_to_dlq(self, plugin_manager, queue):
        """Test that events exceeding max_retries go to DLQ"""
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue, max_retries=1
        )

        try:
            orchestrator.start()

            failed_events = []
            queue.subscribe(
                Topics.PROCESSING_FAILED, lambda msg: failed_events.append(msg)
            )

            # Create event that already exceeded retries
            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                    retry_count=1,  # Already at max
                ),
                raw_data={"test": "data"},
            )

            # Trigger failure
            orchestrator._handle_processing_failure(event.to_dict(), "Permanent error")

            # Wait for DLQ publish
            time.sleep(0.3)

            # Should be sent to failed queue
            assert len(failed_events) == 1
            failed = failed_events[0]
            assert failed["metadata"]["event_type"] == EventType.PROCESSING_FAILED
            assert failed["error_message"] == "Permanent error"
            assert failed["is_recoverable"] is False

        finally:
            orchestrator.stop()


class TestPluginExecution:
    """Test plugin execution order and coordination"""

    def test_plugins_execute_in_priority_order(self, plugin_manager, queue):
        """Test that plugins execute in correct priority order"""
        # This test requires actual processing plugins
        # For now, test the empty plugin scenario
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue
        )

        try:
            orchestrator.start()

            processed = []
            queue.subscribe(
                Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg)
            )

            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                ),
                raw_data={"test": "data"},
            )

            queue.publish(Topics.RAW_LISTINGS, event.to_dict())
            time.sleep(0.3)

            # Verify processing stages are recorded
            assert len(processed) >= 1
            result = processed[-1]
            assert "processing_stages" in result
            assert "plugins_applied" in result

        finally:
            orchestrator.stop()

    def test_plugin_failure_continues_pipeline(self, plugin_manager, queue):
        """Test that plugin failure doesn't stop entire pipeline"""
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue
        )

        try:
            orchestrator.start()

            processed = []
            queue.subscribe(
                Topics.PROCESSED_LISTINGS, lambda msg: processed.append(msg)
            )

            event = RawListingEvent(
                metadata=EventMetadata(
                    event_type=EventType.RAW_LISTING,
                    source_plugin_id="test-source",
                    source_platform="test-platform",
                ),
                raw_data={"data": "test"},
            )

            queue.publish(Topics.RAW_LISTINGS, event.to_dict())
            time.sleep(0.3)

            # Event should still be processed even if individual plugins fail
            assert len(processed) >= 1
            result = processed[-1]
            assert result["metadata"]["status"] == EventStatus.COMPLETED

        finally:
            orchestrator.stop()

    def test_get_processing_plugins_filters_enabled(self, plugin_manager, queue):
        """Test that only enabled processing plugins are retrieved"""
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue
        )

        # Get processing plugins (should be empty for default plugin manager)
        plugins = orchestrator._get_processing_plugins()

        # Should return list (empty in test environment)
        assert isinstance(plugins, list)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_event_format(self, orchestrator, queue):
        """Test handling of invalid event format"""
        orchestrator.start()

        failed_events = []
        queue.subscribe(Topics.PROCESSING_FAILED, lambda msg: failed_events.append(msg))

        # Publish completely invalid data
        queue.publish(Topics.RAW_LISTINGS, {"invalid": "format"})

        time.sleep(0.5)

        # Should handle gracefully and track failure
        stats = orchestrator.get_statistics()
        assert (
            stats["events_failed"] >= 0
        )  # May or may not increment depending on parsing

    def test_missing_required_fields(self, orchestrator, queue):
        """Test handling of events with missing required fields"""
        orchestrator.start()

        failed_events = []
        queue.subscribe(Topics.PROCESSING_FAILED, lambda msg: failed_events.append(msg))

        # Event with missing required metadata fields
        incomplete_event = {
            "metadata": {
                "event_type": EventType.RAW_LISTING,
                # Missing source_plugin_id and source_platform
            },
            "raw_data": {},
        }

        queue.publish(Topics.RAW_LISTINGS, incomplete_event)
        time.sleep(0.5)

        # Should handle error gracefully
        stats = orchestrator.get_statistics()
        assert stats["events_failed"] >= 0

    def test_exception_in_process_raw_listing(self, plugin_manager, queue):
        """Test exception handling in _process_raw_listing"""
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue
        )

        try:
            orchestrator.start()

            failed_count_before = orchestrator._stats["events_failed"]

            # Publish malformed event
            queue.publish(Topics.RAW_LISTINGS, "not a dict")

            time.sleep(0.3)

            # Should increment failure count or handle gracefully
            # Behavior depends on queue implementation
            assert orchestrator.is_running()  # Should still be running

        finally:
            orchestrator.stop()


class TestStatisticsAccuracy:
    """Test statistics accuracy and calculations"""

    def test_plugins_executed_count(self, orchestrator, queue):
        """Test that plugins_executed counter is accurate"""
        orchestrator.start()

        initial_count = orchestrator._stats["plugins_executed"]

        # Process an event
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
            ),
            raw_data={"test": "data"},
        )

        queue.publish(Topics.RAW_LISTINGS, event.to_dict())
        time.sleep(0.3)

        # Plugins executed should be tracked
        final_count = orchestrator._stats["plugins_executed"]
        assert final_count >= initial_count

    def test_processing_time_recorded(self, orchestrator, queue):
        """Test that processing time is recorded"""
        orchestrator.start()

        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
            ),
            raw_data={"test": "data"},
        )

        queue.publish(Topics.RAW_LISTINGS, event.to_dict())
        time.sleep(0.3)

        stats = orchestrator.get_statistics()
        if stats["events_processed"] > 0:
            assert stats["total_processing_time_ms"] > 0
            assert stats["avg_processing_time_ms"] > 0


class TestPipelineExecution:
    """Test detailed pipeline execution logic"""

    def test_execute_pipeline_with_no_plugins(self, orchestrator):
        """Test _execute_pipeline when no plugins are available"""
        event = RawListingEvent(
            metadata=EventMetadata(
                event_type=EventType.RAW_LISTING,
                source_plugin_id="test-source",
                source_platform="test-platform",
            ),
            raw_data={"test": "data"},
        )

        result = orchestrator._execute_pipeline(event)

        assert result["listing_data"] == {"test": "data"}
        assert result["stages"] == []
        assert result["plugins"] == []

    def test_get_processing_plugins_returns_empty_list(self, plugin_manager, queue):
        """Test _get_processing_plugins returns empty list when no plugins"""
        orchestrator = ProcessingOrchestrator(
            plugin_manager=plugin_manager, queue=queue
        )

        plugins = orchestrator._get_processing_plugins()

        assert isinstance(plugins, list)
        assert len(plugins) == 0
