"""
Event Models for Message Queue

Defines event formats for the processing pipeline.
All events follow a standard envelope structure for traceability.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Types of events in the system"""

    RAW_LISTING = "raw_listing"
    NORMALIZED_LISTING = "normalized_listing"
    PROCESSED_LISTING = "processed_listing"
    FRAUD_DETECTED = "fraud_detected"
    LISTING_INDEXED = "listing_indexed"
    PROCESSING_FAILED = "processing_failed"


class EventStatus(str, Enum):
    """Event processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class EventMetadata(BaseModel):
    """
    Metadata for event tracking and tracing.

    Provides full observability across the processing pipeline.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_plugin_id: str
    source_platform: str

    # Tracing (from #20)
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    parent_event_id: Optional[str] = None

    # Processing metadata
    retry_count: int = 0
    max_retries: int = 3
    status: EventStatus = EventStatus.PENDING

    # Additional context
    tags: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0"

    model_config = ConfigDict(use_enum_values=True)


class RawListingEvent(BaseModel):
    """
    Raw listing event from scraper.

    Contains unprocessed data exactly as received from the source,
    along with metadata for processing and tracing.
    """

    metadata: EventMetadata

    # Raw data from source
    raw_data: Dict[str, Any] = Field(
        ..., description="Unparsed data from source (HTML, JSON, XML, etc.)"
    )

    # Source information
    source_url: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    # Original identifiers
    original_id: Optional[str] = None
    external_id: Optional[str] = None

    # Scraping context
    scraper_version: Optional[str] = None
    user_agent: Optional[str] = None
    proxy_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for queue publishing"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RawListingEvent":
        """Create from dictionary (from queue)"""
        return cls.model_validate(data)


class NormalizedListingEvent(BaseModel):
    """
    Normalized listing event after initial processing.

    Data has been parsed and mapped to Unified Data Model (UDM).
    """

    metadata: EventMetadata

    # Normalized data in UDM format
    listing_data: Dict[str, Any] = Field(
        ..., description="Listing data in Unified Data Model format"
    )

    # Validation results
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    is_valid: bool = True

    # Processing stages completed
    processing_stages: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for queue publishing"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedListingEvent":
        """Create from dictionary (from queue)"""
        return cls.model_validate(data)


class ProcessedListingEvent(BaseModel):
    """
    Fully processed listing event ready for storage/indexing.

    All processing plugins have been applied, fraud detection completed.
    """

    metadata: EventMetadata

    # Final processed data
    listing_data: Dict[str, Any] = Field(
        ..., description="Fully processed listing in UDM format"
    )

    # Fraud detection results
    fraud_score: float = Field(ge=0.0, le=100.0)
    fraud_signals: List[str] = Field(default_factory=list)
    risk_level: str = Field(default="unknown")  # safe | suspicious | fraud

    # Processing summary
    processing_stages: List[str] = Field(default_factory=list)
    processing_duration_ms: float = 0.0
    plugins_applied: List[str] = Field(default_factory=list)

    # Quality metrics
    data_quality_score: Optional[float] = None
    completeness_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for queue publishing"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessedListingEvent":
        """Create from dictionary (from queue)"""
        return cls.model_validate(data)


class ProcessingFailedEvent(BaseModel):
    """
    Event for processing failures.

    Captures error details for debugging and recovery.
    """

    metadata: EventMetadata

    # Error information
    error_type: str
    error_message: str
    error_stacktrace: Optional[str] = None

    # Failed stage
    failed_stage: str
    failed_plugin: Optional[str] = None

    # Original event
    original_event: Dict[str, Any] = Field(
        ..., description="Original event that failed processing"
    )

    # Recovery information
    is_recoverable: bool = True
    recovery_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for queue publishing"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingFailedEvent":
        """Create from dictionary (from queue)"""
        return cls.model_validate(data)


class FraudDetectedEvent(BaseModel):
    """
    Event emitted when fraud is detected.

    Used for alerting and investigation.
    """

    metadata: EventMetadata

    # Listing information
    listing_id: str
    listing_url: Optional[str] = None

    # Fraud details
    fraud_score: float = Field(ge=0.0, le=100.0)
    risk_level: str  # suspicious | fraud
    fraud_signals: List[str] = Field(default_factory=list)

    # Detection details
    detected_by: List[str] = Field(
        default_factory=list,
        description="List of detection plugins that flagged this listing",
    )
    confidence: float = Field(ge=0.0, le=1.0)

    # Action taken
    action: str = "flagged"  # flagged | blocked | review_required
    reviewed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for queue publishing"""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FraudDetectedEvent":
        """Create from dictionary (from queue)"""
        return cls.model_validate(data)


# Topic names for queue routing
class Topics:
    """Standard topic names for queue routing"""

    RAW_LISTINGS = "listings.raw"
    NORMALIZED_LISTINGS = "listings.normalized"
    PROCESSED_LISTINGS = "listings.processed"
    FRAUD_DETECTED = "fraud.detected"
    PROCESSING_FAILED = "processing.failed"
    DEAD_LETTER = "dead_letter"

    @classmethod
    def all(cls) -> List[str]:
        """Get all topic names"""
        return [
            cls.RAW_LISTINGS,
            cls.NORMALIZED_LISTINGS,
            cls.PROCESSED_LISTINGS,
            cls.FRAUD_DETECTED,
            cls.PROCESSING_FAILED,
            cls.DEAD_LETTER,
        ]
