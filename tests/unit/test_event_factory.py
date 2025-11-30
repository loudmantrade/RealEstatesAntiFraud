"""
Unit tests for EventFactory.

Tests factory methods for creating messaging events with realistic data.
"""

import uuid

import pytest

from core.models.events import (
    EventStatus,
    EventType,
    FraudDetectedEvent,
    NormalizedListingEvent,
    ProcessedListingEvent,
    RawListingEvent,
)
from tests.factories import EventFactory


class TestEventFactory:
    """Test basic EventFactory functionality."""

    def test_create_raw_event_default(self):
        """Test creating raw event with default values."""
        factory = EventFactory()
        event = factory.create_raw_event()

        assert isinstance(event, RawListingEvent)
        assert event.metadata.event_type == EventType.RAW_LISTING
        assert event.metadata.source_plugin_id is not None
        assert event.metadata.source_platform in factory.PLATFORMS
        assert event.raw_data is not None
        assert "listing_id" in event.raw_data
        assert event.source_url is not None
        assert event.scraped_at is not None

    def test_create_raw_event_with_overrides(self):
        """Test creating raw event with custom values."""
        factory = EventFactory()
        custom_listing_id = str(uuid.uuid4())
        custom_trace_id = str(uuid.uuid4())

        event = factory.create_raw_event(
            listing_id=custom_listing_id,
            trace_id=custom_trace_id,
            source_platform="cian.ru",
        )

        assert event.raw_data["listing_id"] == custom_listing_id
        assert event.metadata.trace_id == custom_trace_id
        assert event.metadata.source_platform == "cian.ru"

    def test_create_raw_event_reproducible_with_seed(self):
        """Test that seed produces reproducible events."""
        factory1 = EventFactory(seed=42)
        event1 = factory1.create_raw_event()

        factory2 = EventFactory(seed=42)
        event2 = factory2.create_raw_event()

        assert event1.raw_data["listing_id"] == event2.raw_data["listing_id"]
        assert event1.metadata.event_id == event2.metadata.event_id
        assert event1.metadata.trace_id == event2.metadata.trace_id


class TestNormalizedEvent:
    """Test NormalizedListingEvent creation."""

    def test_create_normalized_event_default(self):
        """Test creating normalized event with default values."""
        factory = EventFactory()
        event = factory.create_normalized_event()

        assert isinstance(event, NormalizedListingEvent)
        assert event.metadata.event_type == EventType.NORMALIZED_LISTING
        assert event.listing_data is not None
        assert "listing_id" in event.listing_data
        assert event.is_valid is True
        assert len(event.validation_errors) == 0
        assert "validation" in event.processing_stages
        assert "normalization" in event.processing_stages

    def test_create_normalized_event_invalid(self):
        """Test creating invalid normalized event."""
        factory = EventFactory()
        event = factory.create_normalized_event(is_valid=False)

        assert event.is_valid is False
        assert len(event.validation_errors) > 0

    def test_create_normalized_event_with_parent(self):
        """Test creating normalized event with parent event ID."""
        factory = EventFactory()
        parent_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        event = factory.create_normalized_event(
            trace_id=trace_id,
            parent_event_id=parent_id,
        )

        assert event.metadata.trace_id == trace_id
        assert event.metadata.parent_event_id == parent_id
        assert event.metadata.status == EventStatus.COMPLETED


class TestProcessedEvent:
    """Test ProcessedListingEvent creation."""

    def test_create_processed_event_default(self):
        """Test creating processed event with default values."""
        factory = EventFactory()
        event = factory.create_processed_event()

        assert isinstance(event, ProcessedListingEvent)
        assert event.metadata.event_type == EventType.PROCESSED_LISTING
        assert 0 <= event.fraud_score <= 100
        assert event.risk_level in factory.RISK_LEVELS
        assert len(event.processing_stages) >= 3
        assert event.processing_duration_ms > 0
        assert len(event.plugins_applied) >= 2
        assert event.data_quality_score is not None
        assert event.completeness_score is not None

    def test_create_processed_event_with_fraud_score(self):
        """Test creating processed event with specific fraud score."""
        factory = EventFactory()
        event = factory.create_processed_event(fraud_score=85.0)

        assert event.fraud_score == 85.0
        assert event.risk_level == "fraud"
        assert len(event.fraud_signals) >= 0

    def test_create_processed_event_risk_levels(self):
        """Test risk level assignment based on fraud score."""
        factory = EventFactory()

        # Safe
        safe_event = factory.create_processed_event(fraud_score=20.0)
        assert safe_event.risk_level == "safe"

        # Suspicious
        suspicious_event = factory.create_processed_event(fraud_score=50.0)
        assert suspicious_event.risk_level == "suspicious"

        # Fraud
        fraud_event = factory.create_processed_event(fraud_score=80.0)
        assert fraud_event.risk_level == "fraud"

    def test_create_processed_event_fraud_signals(self):
        """Test fraud signals presence based on score."""
        factory = EventFactory(seed=42)

        # Low score - no signals
        low_score_event = factory.create_processed_event(fraud_score=20.0)
        assert len(low_score_event.fraud_signals) == 0

        # High score - has signals
        high_score_event = factory.create_processed_event(fraud_score=80.0)
        assert len(high_score_event.fraud_signals) > 0
        for signal in high_score_event.fraud_signals:
            assert signal in factory.FRAUD_SIGNALS


class TestFraudDetectedEvent:
    """Test FraudDetectedEvent creation."""

    def test_create_fraud_detected_event_default(self):
        """Test creating fraud detected event with default values."""
        factory = EventFactory()
        event = factory.create_fraud_detected_event()

        assert isinstance(event, FraudDetectedEvent)
        assert event.metadata.event_type == EventType.FRAUD_DETECTED
        assert event.fraud_score >= 70
        assert event.risk_level in ["suspicious", "fraud"]
        assert len(event.fraud_signals) >= 2
        assert len(event.detected_by) >= 1
        assert 0.7 <= event.confidence <= 1.0
        assert event.action in ["flagged", "blocked", "review_required"]
        assert event.reviewed is False

    def test_create_fraud_detected_event_high_score(self):
        """Test fraud event with very high score."""
        factory = EventFactory()
        event = factory.create_fraud_detected_event(fraud_score=95.0)

        assert event.fraud_score == 95.0
        assert event.risk_level == "fraud"

    def test_create_fraud_detected_event_suspicious(self):
        """Test fraud event with suspicious level."""
        factory = EventFactory()
        event = factory.create_fraud_detected_event(fraud_score=75.0)

        assert event.fraud_score == 75.0
        assert event.risk_level == "suspicious"


class TestEventChain:
    """Test event chain creation."""

    def test_create_event_chain_default(self):
        """Test creating complete event chain."""
        factory = EventFactory(seed=42)
        chain = factory.create_event_chain()

        # Should have 4 events (raw, normalized, processed, fraud)
        assert len(chain) == 4
        assert isinstance(chain[0], RawListingEvent)
        assert isinstance(chain[1], NormalizedListingEvent)
        assert isinstance(chain[2], ProcessedListingEvent)
        assert isinstance(chain[3], FraudDetectedEvent)

    def test_create_event_chain_without_fraud(self):
        """Test creating chain without fraud event."""
        factory = EventFactory(seed=42)
        chain = factory.create_event_chain(include_fraud=False)

        # Should have 3 events (raw, normalized, processed)
        assert len(chain) == 3
        assert isinstance(chain[0], RawListingEvent)
        assert isinstance(chain[1], NormalizedListingEvent)
        assert isinstance(chain[2], ProcessedListingEvent)

    def test_event_chain_correlation(self):
        """Test that events in chain are properly correlated."""
        factory = EventFactory()
        chain = factory.create_event_chain()

        # All events should have same trace_id
        trace_id = chain[0].metadata.trace_id
        for event in chain:
            assert event.metadata.trace_id == trace_id

        # Each event should reference previous event as parent
        for i in range(1, len(chain)):
            assert chain[i].metadata.parent_event_id == chain[i - 1].metadata.event_id

    def test_event_chain_same_listing(self):
        """Test that all events in chain reference same listing."""
        factory = EventFactory()
        listing_id = str(uuid.uuid4())
        chain = factory.create_event_chain(listing_id=listing_id)

        # Raw event
        assert chain[0].raw_data["listing_id"] == listing_id

        # Normalized event
        assert chain[1].listing_data["listing_id"] == listing_id

        # Processed event
        assert chain[2].listing_data["listing_id"] == listing_id

        # Fraud event (if present)
        if len(chain) > 3:
            assert chain[3].listing_id == listing_id

    def test_event_chain_chronological_timestamps(self):
        """Test that events have chronological timestamps."""
        factory = EventFactory()
        chain = factory.create_event_chain()

        timestamps = [event.metadata.timestamp for event in chain]
        for i in range(len(timestamps) - 1):
            assert timestamps[i] < timestamps[i + 1]


class TestBatchCreation:
    """Test batch event creation."""

    def test_create_batch_raw_events(self):
        """Test creating batch of raw events."""
        factory = EventFactory()
        events = factory.create_batch(5, event_type="raw")

        assert len(events) == 5
        for event in events:
            assert isinstance(event, RawListingEvent)

        # All events should have unique IDs
        event_ids = [event.metadata.event_id for event in events]
        assert len(event_ids) == len(set(event_ids))

    def test_create_batch_normalized_events(self):
        """Test creating batch of normalized events."""
        factory = EventFactory()
        events = factory.create_batch(3, event_type="normalized")

        assert len(events) == 3
        for event in events:
            assert isinstance(event, NormalizedListingEvent)

    def test_create_batch_processed_events(self):
        """Test creating batch of processed events."""
        factory = EventFactory()
        events = factory.create_batch(4, event_type="processed")

        assert len(events) == 4
        for event in events:
            assert isinstance(event, ProcessedListingEvent)

    def test_create_batch_with_common_params(self):
        """Test creating batch with shared parameters."""
        factory = EventFactory()
        trace_id = str(uuid.uuid4())
        events = factory.create_batch(
            3,
            event_type="raw",
            trace_id=trace_id,
            source_platform="cian.ru",
        )

        for event in events:
            assert event.metadata.trace_id == trace_id
            assert event.metadata.source_platform == "cian.ru"

    def test_create_batch_invalid_type(self):
        """Test creating batch with invalid event type."""
        factory = EventFactory()

        with pytest.raises(ValueError, match="Unknown event_type"):
            factory.create_batch(5, event_type="invalid")


class TestMetadataGeneration:
    """Test event metadata generation."""

    def test_metadata_has_required_fields(self):
        """Test that metadata contains all required fields."""
        factory = EventFactory()
        event = factory.create_raw_event()
        metadata = event.metadata

        assert metadata.event_id is not None
        assert metadata.event_type is not None
        assert metadata.timestamp is not None
        assert metadata.source_plugin_id is not None
        assert metadata.source_platform is not None
        assert metadata.trace_id is not None
        assert metadata.request_id is not None
        assert metadata.status is not None
        assert metadata.retry_count == 0
        assert metadata.max_retries == 3
        assert metadata.version == "1.0"

    def test_metadata_trace_propagation(self):
        """Test trace ID propagation across events."""
        factory = EventFactory()
        trace_id = str(uuid.uuid4())

        raw = factory.create_raw_event(trace_id=trace_id)
        normalized = factory.create_normalized_event(
            trace_id=trace_id, parent_event_id=raw.metadata.event_id
        )
        processed = factory.create_processed_event(
            trace_id=trace_id, parent_event_id=normalized.metadata.event_id
        )

        assert raw.metadata.trace_id == trace_id
        assert normalized.metadata.trace_id == trace_id
        assert processed.metadata.trace_id == trace_id

    def test_metadata_tags(self):
        """Test metadata tags are present."""
        factory = EventFactory()
        event = factory.create_raw_event()

        assert "environment" in event.metadata.tags
        assert event.metadata.tags["environment"] == "test"


class TestDataRealism:
    """Test realistic data generation."""

    def test_platforms_are_realistic(self):
        """Test that source platforms are real estate sites."""
        factory = EventFactory(seed=42)
        events = factory.create_batch(10, event_type="raw")

        platforms = [event.metadata.source_platform for event in events]
        for platform in platforms:
            assert platform in factory.PLATFORMS

    def test_fraud_signals_are_realistic(self):
        """Test that fraud signals are from predefined list."""
        factory = EventFactory(seed=42)
        events = [factory.create_processed_event(fraud_score=80.0) for _ in range(10)]

        for event in events:
            for signal in event.fraud_signals:
                assert signal in factory.FRAUD_SIGNALS

    def test_processing_stages_are_valid(self):
        """Test that processing stages are from predefined list."""
        factory = EventFactory(seed=42)
        events = factory.create_batch(10, event_type="processed")

        for event in events:
            for stage in event.processing_stages:
                assert stage in factory.PROCESSING_STAGES

    def test_listing_data_structure(self):
        """Test that listing data has proper UDM structure."""
        factory = EventFactory()
        event = factory.create_normalized_event()
        listing = event.listing_data

        # Required UDM fields
        assert "listing_id" in listing
        assert "source" in listing
        assert "type" in listing
        assert "property_type" in listing
        assert "location" in listing
        assert "price" in listing

        # Location structure
        assert "city" in listing["location"]
        assert "coordinates" in listing["location"]

        # Price structure
        assert "amount" in listing["price"]
        assert "currency" in listing["price"]
        assert listing["price"]["currency"] == "RUB"


class TestFactoryConsistency:
    """Test factory consistency and reliability."""

    def test_multiple_chains_unique_ids(self):
        """Test that multiple chains have unique correlation IDs."""
        factory = EventFactory()
        chain1 = factory.create_event_chain()
        chain2 = factory.create_event_chain()

        assert chain1[0].metadata.trace_id != chain2[0].metadata.trace_id
        assert chain1[0].metadata.event_id != chain2[0].metadata.event_id

    def test_timestamp_progression(self):
        """Test that timestamps progress across multiple events."""
        factory = EventFactory()

        # Create multiple events
        events = [factory.create_raw_event() for _ in range(5)]

        # Each event should have later timestamp than previous
        for i in range(len(events) - 1):
            assert events[i].metadata.timestamp < events[i + 1].metadata.timestamp

    def test_fraud_score_range_validation(self):
        """Test fraud scores are always in valid range."""
        factory = EventFactory(seed=42)

        # Create many events to test range
        processed_events = factory.create_batch(50, event_type="processed")
        fraud_events = [factory.create_fraud_detected_event() for _ in range(50)]

        for event in processed_events:
            assert 0 <= event.fraud_score <= 100

        for event in fraud_events:
            assert 70 <= event.fraud_score <= 100
