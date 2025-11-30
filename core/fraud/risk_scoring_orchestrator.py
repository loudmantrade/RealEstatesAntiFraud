"""Risk scoring orchestrator for fraud detection."""

import logging
import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from core.interfaces.detection_plugin import (
    DetectionPlugin,
    DetectionResult,
    RiskSignal,
)

logger = logging.getLogger(__name__)


class FraudScore(BaseModel):
    """Final fraud score for a listing.

    Attributes:
        listing_id: ID of the analyzed listing
        overall_score: Aggregated fraud score from 0.0 (clean) to 100.0 (fraud)
        confidence: Overall confidence level from 0.0 to 1.0
        risk_level: Human-readable risk level (low, medium, high, critical)
        signals: All risk signals from detection plugins
        plugin_results: Results from each detection plugin
        processing_time_ms: Total processing time in milliseconds
        metadata: Additional context and statistics
    """

    listing_id: str
    overall_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: str
    signals: List[RiskSignal] = Field(default_factory=list)
    plugin_results: List[DetectionResult] = Field(default_factory=list)
    processing_time_ms: float = Field(ge=0.0)
    metadata: Dict = Field(default_factory=dict)


class RiskScoringOrchestrator:
    """Orchestrator for fraud detection plugins.

    Aggregates risk signals from multiple detection plugins and computes
    a final fraud score using weighted averaging.

    Attributes:
        detection_plugins: List of registered detection plugins
        min_confidence_threshold: Minimum confidence to include a signal (default: 0.5)
    """

    def __init__(
        self,
        detection_plugins: Optional[List[DetectionPlugin]] = None,
        min_confidence_threshold: float = 0.5,
    ):
        """Initialize the risk scoring orchestrator.

        Args:
            detection_plugins: List of detection plugins to use
            min_confidence_threshold: Minimum confidence for signal inclusion
        """
        self.detection_plugins = detection_plugins or []
        self.min_confidence_threshold = min_confidence_threshold
        logger.info(f"Initialized RiskScoringOrchestrator with {len(self.detection_plugins)} plugins")

    def register_plugin(self, plugin: DetectionPlugin) -> None:
        """Register a detection plugin.

        Args:
            plugin: Detection plugin to register
        """
        if plugin not in self.detection_plugins:
            self.detection_plugins.append(plugin)
            metadata = plugin.get_metadata()
            logger.info(f"Registered detection plugin: {metadata.get('id')}")

    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a detection plugin.

        Args:
            plugin_id: ID of the plugin to unregister

        Returns:
            True if plugin was removed, False if not found
        """
        for plugin in self.detection_plugins:
            metadata = plugin.get_metadata()
            if metadata.get("id") == plugin_id:
                self.detection_plugins.remove(plugin)
                logger.info(f"Unregistered detection plugin: {plugin_id}")
                return True
        return False

    async def run(self, listing: Dict) -> FraudScore:
        """Analyze listing and compute fraud score.

        Runs all registered detection plugins, aggregates their signals,
        and computes a final weighted fraud score.

        Args:
            listing: Listing data to analyze

        Returns:
            FraudScore with overall score and risk signals
        """
        start_time = time.time()
        listing_id = listing.get("listing_id", "unknown")

        logger.info(f"Starting fraud analysis for listing: {listing_id}")

        # Run all detection plugins concurrently
        plugin_results: List[DetectionResult] = []
        all_signals: List[RiskSignal] = []

        # Create tasks for all plugins
        async def run_plugin_safe(plugin: DetectionPlugin) -> Optional[DetectionResult]:
            """Run plugin with error handling."""
            try:
                metadata = plugin.get_metadata()
                plugin_id = metadata.get("id", "unknown")

                logger.debug(f"Running detection plugin: {plugin_id}")
                result = await plugin.analyze(listing)

                logger.debug(
                    f"Plugin {plugin_id}: score={result.overall_score:.2f}, "
                    f"signals={len(result.signals)}, time={result.processing_time_ms:.1f}ms"
                )
                return result

            except Exception as e:
                plugin_id = plugin.get_metadata().get("id", "unknown")
                logger.error(f"Error running detection plugin {plugin_id}: {e}", exc_info=True)
                return None

        # Execute all plugins concurrently
        import asyncio

        results = await asyncio.gather(
            *[run_plugin_safe(plugin) for plugin in self.detection_plugins],
            return_exceptions=False,
        )

        # Process results and collect signals
        for result in results:
            if result is not None:
                plugin_results.append(result)

                # Collect signals that meet confidence threshold
                for signal in result.signals:
                    if signal.confidence >= self.min_confidence_threshold:
                        all_signals.append(signal)

        # Compute weighted fraud score
        overall_score, confidence = self._compute_weighted_score(plugin_results)

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)

        # Calculate total processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Build metadata
        metadata = {
            "plugins_executed": len(plugin_results),
            "total_signals": len(all_signals),
            "high_confidence_signals": sum(1 for s in all_signals if s.confidence > 0.8),
            "plugin_scores": [{"plugin_id": r.plugin_id, "score": r.overall_score} for r in plugin_results],
        }

        fraud_score = FraudScore(
            listing_id=listing_id,
            overall_score=overall_score,
            confidence=confidence,
            risk_level=risk_level,
            signals=all_signals,
            plugin_results=plugin_results,
            processing_time_ms=processing_time_ms,
            metadata=metadata,
        )

        logger.info(
            f"Fraud analysis complete for {listing_id}: "
            f"score={overall_score:.1f}, risk={risk_level}, "
            f"signals={len(all_signals)}, time={processing_time_ms:.1f}ms"
        )

        return fraud_score

    def _compute_weighted_score(self, plugin_results: List[DetectionResult]) -> tuple[float, float]:
        """Compute weighted average fraud score from plugin results.

        Args:
            plugin_results: Results from detection plugins

        Returns:
            Tuple of (overall_score, confidence) where score is 0-100
        """
        if not plugin_results:
            return 0.0, 0.0

        # Get plugin weights
        weights = []
        scores = []
        confidences = []

        for result in plugin_results:
            # Find corresponding plugin to get weight
            plugin = next(
                (p for p in self.detection_plugins if p.get_metadata().get("id") == result.plugin_id),
                None,
            )

            if plugin:
                weight = plugin.get_weight()
                weights.append(weight)
                scores.append(result.overall_score)

                # Calculate average confidence from signals
                if result.signals:
                    avg_confidence = sum(s.confidence for s in result.signals) / len(result.signals)
                    confidences.append(avg_confidence)
                else:
                    confidences.append(0.0)

        if not weights:
            return 0.0, 0.0

        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0, 0.0

        normalized_weights = [w / total_weight for w in weights]

        # Compute weighted average score (0-1 scale)
        weighted_score = sum(score * weight for score, weight in zip(scores, normalized_weights))

        # Compute weighted average confidence
        weighted_confidence = sum(conf * weight for conf, weight in zip(confidences, normalized_weights))

        # Convert to 0-100 scale
        overall_score = weighted_score * 100.0

        return overall_score, weighted_confidence

    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from fraud score.

        Implements the classification from ARCHITECTURE.md:
        - safe: score < 30
        - suspicious: 30 <= score < 70
        - fraud: score >= 70

        Args:
            score: Fraud score from 0.0 to 100.0

        Returns:
            Risk level: 'safe', 'suspicious', or 'fraud'
        """
        if score < 30.0:
            return "safe"
        elif score < 70.0:
            return "suspicious"
        else:
            return "fraud"

    def get_statistics(self) -> Dict:
        """Get orchestrator statistics.

        Returns:
            Dictionary with plugin counts and configuration
        """
        return {
            "plugins_registered": len(self.detection_plugins),
            "plugin_ids": [p.get_metadata().get("id") for p in self.detection_plugins],
            "min_confidence_threshold": self.min_confidence_threshold,
        }
