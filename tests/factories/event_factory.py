"""
EventFactory for generating messaging event test data.

This factory creates realistic event objects for all event types in the
messaging pipeline (RawListingEvent, NormalizedListingEvent,
ProcessedListingEvent, FraudDetectedEvent).

Supports creating:
- Individual events with customization
- Event chains showing complete pipeline flow
- Realistic timestamps in chronological order
- Proper correlation and tracing IDs
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from faker import Faker

from core.models.events import (
    EventMetadata,
    EventStatus,
    EventType,
    FraudDetectedEvent,
    NormalizedListingEvent,
    ProcessedListingEvent,
    RawListingEvent,
)


class EventFactory:
    """
    Factory for generating messaging event test data.

    Creates realistic event objects with proper metadata, tracing,
    and chronological timestamps. Supports creating event chains
    that simulate the complete processing pipeline.

    Example:
        >>> factory = EventFactory(seed=42)
        >>> raw_event = factory.create_raw_event()
        >>> chain = factory.create_event_chain()
        >>> len(chain)  # Returns 4 events
        4
    """

    # Common source platforms
    PLATFORMS = ["cian.ru", "avito.ru", "domofond.ru", "yandex.ru/realty"]

    # Processing stages
    PROCESSING_STAGES = [
        "validation",
        "normalization",
        "deduplication",
        "enrichment",
        "fraud_detection",
    ]

    # Fraud signals
    FRAUD_SIGNALS = [
        "price_too_low",
        "price_too_high",
        "duplicate_images",
        "fake_location",
        "suspicious_description",
        "missing_contact",
        "too_many_listings",
        "rapid_price_changes",
    ]

    # Risk levels
    RISK_LEVELS = ["safe", "suspicious", "fraud"]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize EventFactory.

        Args:
            seed: Optional seed for reproducible test data
        """
        self.faker = Faker("ru_RU")
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            self.faker.seed_instance(seed)

        # Track time for chronological events
        self._current_time = datetime.now(timezone.utc)

    def _next_timestamp(self, seconds: float = None) -> datetime:
        """
        Get next chronological timestamp.

        Args:
            seconds: Optional seconds to advance (random 1-5 if not provided)

        Returns:
            Next timestamp in chronological order
        """
        if seconds is None:
            seconds = random.uniform(1, 5)

        self._current_time += timedelta(seconds=seconds)
        return self._current_time

    def _generate_metadata(
        self,
        event_type: EventType,
        source_plugin_id: Optional[str] = None,
        source_platform: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        status: EventStatus = EventStatus.PENDING,
        **overrides,
    ) -> EventMetadata:
        """
        Generate event metadata with tracing information.

        Args:
            event_type: Type of event
            source_plugin_id: Plugin ID (generated if not provided)
            source_platform: Platform name (generated if not provided)
            trace_id: Trace ID for correlation
            parent_event_id: Parent event ID for chaining
            status: Event status
            **overrides: Additional metadata overrides

        Returns:
            EventMetadata instance
        """
        if source_platform is None:
            source_platform = random.choice(self.PLATFORMS)

        if source_plugin_id is None:
            source_plugin_id = f"{source_platform.split('.')[0]}_plugin"

        metadata = {
            "event_id": self.faker.uuid4(),
            "event_type": event_type,
            "timestamp": self._next_timestamp(),
            "source_plugin_id": source_plugin_id,
            "source_platform": source_platform,
            "trace_id": trace_id or self.faker.uuid4(),
            "request_id": self.faker.uuid4(),
            "parent_event_id": parent_event_id,
            "status": status,
            "retry_count": 0,
            "max_retries": 3,
            "tags": {"environment": "test"},
            "version": "1.0",
        }

        metadata.update(overrides)
        return EventMetadata(**metadata)

    def create_raw_event(
        self,
        listing_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        **overrides,
    ) -> RawListingEvent:
        """
        Create a RawListingEvent with realistic data.

        Args:
            listing_id: Optional listing ID
            trace_id: Optional trace ID for correlation
            **overrides: Field overrides

        Returns:
            RawListingEvent instance

        Example:
            >>> factory = EventFactory()
            >>> event = factory.create_raw_event()
            >>> event.metadata.event_type
            EventType.RAW_LISTING
        """
        if listing_id is None:
            listing_id = self.faker.uuid4()

        platform = overrides.pop("source_platform", random.choice(self.PLATFORMS))

        metadata = self._generate_metadata(
            event_type=EventType.RAW_LISTING,
            source_platform=platform,
            trace_id=trace_id,
            **overrides.pop("metadata", {}),
        )

        raw_data = overrides.pop(
            "raw_data",
            {
                "listing_id": listing_id,
                "title": self.faker.sentence(nb_words=6),
                "price": random.randint(1_000_000, 20_000_000),
                "area": random.randint(30, 150),
                "rooms": random.randint(1, 4),
                "address": self.faker.address(),
                "description": self.faker.text(max_nb_chars=200),
                "images": [
                    self.faker.image_url() for _ in range(random.randint(3, 10))
                ],
            },
        )

        event_data = {
            "metadata": metadata,
            "raw_data": raw_data,
            "source_url": f"https://{platform}/listing/{listing_id}",
            "scraped_at": self._next_timestamp(),
            "original_id": listing_id,
            "external_id": self.faker.uuid4(),
            "scraper_version": "1.0.0",
            "user_agent": self.faker.user_agent(),
            "proxy_used": None,
        }

        event_data.update(overrides)
        return RawListingEvent(**event_data)

    def create_normalized_event(
        self,
        listing_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        is_valid: bool = True,
        **overrides,
    ) -> NormalizedListingEvent:
        """
        Create a NormalizedListingEvent with UDM data.

        Args:
            listing_id: Optional listing ID
            trace_id: Optional trace ID for correlation
            parent_event_id: Optional parent event ID
            is_valid: Whether listing data is valid
            **overrides: Field overrides

        Returns:
            NormalizedListingEvent instance

        Example:
            >>> factory = EventFactory()
            >>> event = factory.create_normalized_event()
            >>> event.is_valid
            True
        """
        if listing_id is None:
            listing_id = self.faker.uuid4()

        metadata = self._generate_metadata(
            event_type=EventType.NORMALIZED_LISTING,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            status=EventStatus.COMPLETED,
            **overrides.pop("metadata", {}),
        )

        listing_data = overrides.pop(
            "listing_data",
            {
                "listing_id": listing_id,
                "source": {
                    "plugin_id": metadata.source_plugin_id,
                    "platform": metadata.source_platform,
                    "original_id": self.faker.uuid4(),
                    "url": f"https://{metadata.source_platform}/listing/{listing_id}",
                },
                "type": random.choice(["sale", "rent"]),
                "property_type": random.choice(
                    ["apartment", "house", "commercial", "land"]
                ),
                "location": {
                    "city": random.choice(
                        ["Москва", "Санкт-Петербург", "Екатеринбург"]
                    ),
                    "coordinates": {
                        "latitude": random.uniform(55.0, 60.0),
                        "longitude": random.uniform(30.0, 40.0),
                    },
                },
                "price": {
                    "amount": random.uniform(1_000_000, 20_000_000),
                    "currency": "RUB",
                },
            },
        )

        event_data = {
            "metadata": metadata,
            "listing_data": listing_data,
            "validation_errors": [] if is_valid else ["Invalid price format"],
            "validation_warnings": [],
            "is_valid": is_valid,
            "processing_stages": ["validation", "normalization"],
        }

        event_data.update(overrides)
        return NormalizedListingEvent(**event_data)

    def create_processed_event(
        self,
        listing_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        fraud_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        **overrides,
    ) -> ProcessedListingEvent:
        """
        Create a ProcessedListingEvent with fraud analysis.

        Args:
            listing_id: Optional listing ID
            trace_id: Optional trace ID for correlation
            parent_event_id: Optional parent event ID
            fraud_score: Optional fraud score (0-100)
            risk_level: Optional risk level (safe/suspicious/fraud)
            **overrides: Field overrides

        Returns:
            ProcessedListingEvent instance

        Example:
            >>> factory = EventFactory()
            >>> event = factory.create_processed_event(fraud_score=75.0)
            >>> event.fraud_score
            75.0
        """
        if listing_id is None:
            listing_id = self.faker.uuid4()

        if fraud_score is None:
            fraud_score = random.uniform(0, 100)

        if risk_level is None:
            if fraud_score < 30:
                risk_level = "safe"
            elif fraud_score < 70:
                risk_level = "suspicious"
            else:
                risk_level = "fraud"

        metadata = self._generate_metadata(
            event_type=EventType.PROCESSED_LISTING,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            status=EventStatus.COMPLETED,
            **overrides.pop("metadata", {}),
        )

        listing_data = overrides.pop(
            "listing_data",
            {
                "listing_id": listing_id,
                "source": {
                    "plugin_id": metadata.source_plugin_id,
                    "platform": metadata.source_platform,
                    "original_id": self.faker.uuid4(),
                    "url": f"https://{metadata.source_platform}/listing/{listing_id}",
                },
                "type": random.choice(["sale", "rent"]),
                "property_type": random.choice(
                    ["apartment", "house", "commercial", "land"]
                ),
                "location": {
                    "city": random.choice(
                        ["Москва", "Санкт-Петербург", "Екатеринбург"]
                    ),
                    "coordinates": {
                        "latitude": random.uniform(55.0, 60.0),
                        "longitude": random.uniform(30.0, 40.0),
                    },
                },
                "price": {
                    "amount": random.uniform(1_000_000, 20_000_000),
                    "currency": "RUB",
                },
                "fraud_score": fraud_score,
            },
        )

        num_signals = random.randint(0, 3) if fraud_score > 50 else 0
        fraud_signals = random.sample(self.FRAUD_SIGNALS, num_signals)

        event_data = {
            "metadata": metadata,
            "listing_data": listing_data,
            "fraud_score": fraud_score,
            "fraud_signals": fraud_signals,
            "risk_level": risk_level,
            "processing_stages": random.sample(
                self.PROCESSING_STAGES, random.randint(3, 5)
            ),
            "processing_duration_ms": random.uniform(50, 500),
            "plugins_applied": [f"plugin_{i}" for i in range(random.randint(2, 5))],
            "data_quality_score": random.uniform(0.7, 1.0),
            "completeness_score": random.uniform(0.8, 1.0),
        }

        event_data.update(overrides)
        return ProcessedListingEvent(**event_data)

    def create_fraud_detected_event(
        self,
        listing_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        fraud_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        **overrides,
    ) -> FraudDetectedEvent:
        """
        Create a FraudDetectedEvent for high-risk listings.

        Args:
            listing_id: Optional listing ID
            trace_id: Optional trace ID for correlation
            parent_event_id: Optional parent event ID
            fraud_score: Optional fraud score (70-100)
            risk_level: Optional risk level (suspicious/fraud)
            **overrides: Field overrides

        Returns:
            FraudDetectedEvent instance

        Example:
            >>> factory = EventFactory()
            >>> event = factory.create_fraud_detected_event()
            >>> event.fraud_score >= 70
            True
        """
        if listing_id is None:
            listing_id = self.faker.uuid4()

        if fraud_score is None:
            fraud_score = random.uniform(70, 100)

        if risk_level is None:
            risk_level = "fraud" if fraud_score >= 85 else "suspicious"

        metadata = self._generate_metadata(
            event_type=EventType.FRAUD_DETECTED,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            status=EventStatus.COMPLETED,
            **overrides.pop("metadata", {}),
        )

        platform = metadata.source_platform
        num_signals = random.randint(2, 5)
        fraud_signals = random.sample(self.FRAUD_SIGNALS, num_signals)

        event_data = {
            "metadata": metadata,
            "listing_id": listing_id,
            "listing_url": f"https://{platform}/listing/{listing_id}",
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "fraud_signals": fraud_signals,
            "detected_by": [f"fraud_detector_{i}" for i in range(random.randint(1, 3))],
            "confidence": random.uniform(0.7, 1.0),
            "action": random.choice(["flagged", "blocked", "review_required"]),
            "reviewed": False,
        }

        event_data.update(overrides)
        return FraudDetectedEvent(**event_data)

    def create_event_chain(
        self, listing_id: Optional[str] = None, include_fraud: bool = True
    ) -> List[
        RawListingEvent
        | NormalizedListingEvent
        | ProcessedListingEvent
        | FraudDetectedEvent
    ]:
        """
        Create a complete event chain simulating the processing pipeline.

        The chain represents:
        1. RawListingEvent - Initial scraping
        2. NormalizedListingEvent - After normalization
        3. ProcessedListingEvent - After fraud detection
        4. FraudDetectedEvent - If fraud detected (optional)

        Args:
            listing_id: Optional listing ID (same for all events)
            include_fraud: Whether to include FraudDetectedEvent

        Returns:
            List of events in chronological order

        Example:
            >>> factory = EventFactory(seed=42)
            >>> chain = factory.create_event_chain()
            >>> len(chain)
            4
            >>> chain[0].metadata.event_type
            EventType.RAW_LISTING
            >>> chain[-1].metadata.event_type
            EventType.FRAUD_DETECTED
        """
        if listing_id is None:
            listing_id = self.faker.uuid4()

        # Generate correlation IDs
        trace_id = self.faker.uuid4()

        # 1. Raw event (scraping)
        raw_event = self.create_raw_event(
            listing_id=listing_id,
            trace_id=trace_id,
        )

        # 2. Normalized event (processing)
        normalized_event = self.create_normalized_event(
            listing_id=listing_id,
            trace_id=trace_id,
            parent_event_id=raw_event.metadata.event_id,
        )

        # 3. Processed event (fraud detection)
        fraud_score = (
            random.uniform(70, 100) if include_fraud else random.uniform(0, 69)
        )
        processed_event = self.create_processed_event(
            listing_id=listing_id,
            trace_id=trace_id,
            parent_event_id=normalized_event.metadata.event_id,
            fraud_score=fraud_score,
        )

        events = [raw_event, normalized_event, processed_event]

        # 4. Fraud detected event (if high risk)
        if include_fraud and fraud_score >= 70:
            fraud_event = self.create_fraud_detected_event(
                listing_id=listing_id,
                trace_id=trace_id,
                parent_event_id=processed_event.metadata.event_id,
                fraud_score=fraud_score,
            )
            events.append(fraud_event)

        return events

    def create_batch(
        self, count: int, event_type: str = "raw", **kwargs
    ) -> List[RawListingEvent | NormalizedListingEvent | ProcessedListingEvent]:
        """
        Create multiple events of the same type.

        Args:
            count: Number of events to create
            event_type: Type of event (raw/normalized/processed)
            **kwargs: Arguments passed to event creation method

        Returns:
            List of events

        Example:
            >>> factory = EventFactory()
            >>> events = factory.create_batch(5, event_type="raw")
            >>> len(events)
            5
        """
        if event_type == "raw":
            return [self.create_raw_event(**kwargs) for _ in range(count)]
        elif event_type == "normalized":
            return [self.create_normalized_event(**kwargs) for _ in range(count)]
        elif event_type == "processed":
            return [self.create_processed_event(**kwargs) for _ in range(count)]
        else:
            raise ValueError(
                f"Unknown event_type: {event_type}. "
                "Use 'raw', 'normalized', or 'processed'"
            )
