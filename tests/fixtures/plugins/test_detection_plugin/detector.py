"""Test detection plugin for integration testing."""

import time
from typing import Any, Dict

from core.interfaces.detection_plugin import (
    DetectionPlugin,
    DetectionResult,
    RiskSignal,
)


class TestDetectionPlugin(DetectionPlugin):
    """Test detection plugin that detects price anomalies and duplicates.

    This plugin demonstrates basic fraud detection:
    1. Price anomaly detection (unrealistic prices)
    2. Duplicate listing detection (seen IDs)
    3. Risk signal generation with scores
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the plugin with configuration.

        Args:
            config: Plugin configuration dictionary with:
                - price_threshold_multiplier: Float for price anomaly detection (default: 2.0)
                - enable_duplicate_check: Boolean to enable duplicate detection (default: True)
        """
        self.config = config or {}
        self.price_threshold_multiplier = self.config.get("price_threshold_multiplier", 2.0)
        self.enable_duplicate_check = self.config.get("enable_duplicate_check", True)

        # Track seen listings for duplicate detection
        self.seen_ids = set()
        self.analysis_count = 0

        # Average market price for anomaly detection (simplified)
        self.average_price = 5_000_000  # 5M rubles

    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "id": "plugin-detection-test",
            "name": "Test Detection Plugin",
            "version": "1.0.0",
            "type": "detection",
            "description": "Test detection plugin for integration testing",
            "capabilities": ["price_anomaly_detection", "basic_fraud_signals"],
            "analysis_count": self.analysis_count,
        }

    async def analyze(self, listing: Dict[str, Any]) -> DetectionResult:
        """Analyze a listing for fraud indicators.

        Args:
            listing: Listing data dictionary

        Returns:
            DetectionResult with signals and overall score
        """
        start_time = time.time()
        self.analysis_count += 1

        signals = []

        # Check for price anomalies
        if "price" in listing and listing["price"] is not None:
            price = listing["price"]
            threshold = self.average_price * self.price_threshold_multiplier

            if price > threshold:
                signals.append(
                    RiskSignal(
                        signal_type="price_anomaly",
                        score=0.7,
                        confidence=0.8,
                        reason=f"Price {price:,.0f} exceeds threshold {threshold:,.0f}",
                        metadata={
                            "price": price,
                            "threshold": threshold,
                            "average_price": self.average_price,
                        },
                    )
                )
            elif price < 0:
                signals.append(
                    RiskSignal(
                        signal_type="invalid_price",
                        score=0.9,
                        confidence=1.0,
                        reason="Negative price is invalid",
                        metadata={"price": price},
                    )
                )

        # Check for duplicate listings
        if self.enable_duplicate_check:
            listing_id = listing.get("id") or listing.get("listing_id")
            if listing_id:
                if listing_id in self.seen_ids:
                    signals.append(
                        RiskSignal(
                            signal_type="duplicate_listing",
                            score=0.6,
                            confidence=0.9,
                            reason=f"Listing ID {listing_id} already seen",
                            metadata={"listing_id": listing_id},
                        )
                    )
                else:
                    self.seen_ids.add(listing_id)

        # Calculate overall score (max of individual signals)
        overall_score = max([s.score for s in signals], default=0.0)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        return DetectionResult(
            plugin_id="plugin-detection-test",
            signals=signals,
            overall_score=overall_score,
            processing_time_ms=processing_time_ms,
        )

    def get_weight(self) -> float:
        """Return plugin weight for score aggregation."""
        return 0.5

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        self.seen_ids.clear()
        self.analysis_count = 0
