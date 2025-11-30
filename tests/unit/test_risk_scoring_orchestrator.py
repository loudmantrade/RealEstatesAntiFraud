"""Unit tests for RiskScoringOrchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.fraud.risk_scoring_orchestrator import (
    FraudScore,
    RiskScoringOrchestrator,
)
from core.interfaces.detection_plugin import (
    DetectionPlugin,
    DetectionResult,
    RiskSignal,
)

pytestmark = pytest.mark.unit


class MockDetectionPlugin(DetectionPlugin):
    """Mock detection plugin for testing."""

    def __init__(
        self,
        plugin_id: str,
        weight: float = 0.5,
        score: float = 0.5,
        signals: list = None,
    ):
        self.plugin_id = plugin_id
        self.weight = weight
        self.score = score
        self.signals = signals or []

    def get_metadata(self):
        return {
            "id": self.plugin_id,
            "name": f"Mock Plugin {self.plugin_id}",
            "version": "1.0.0",
            "description": "Mock detection plugin for testing",
        }

    async def analyze(self, listing):
        await asyncio.sleep(0.01)  # Simulate processing
        return DetectionResult(
            plugin_id=self.plugin_id,
            signals=self.signals,
            overall_score=self.score,
            processing_time_ms=10.0,
        )

    def get_weight(self):
        return self.weight


class TestRiskScoringOrchestrator:
    """Test suite for RiskScoringOrchestrator."""

    @pytest.fixture
    def sample_listing(self):
        """Sample listing for testing."""
        return {
            "listing_id": "test-123",
            "price": 1000000,
            "location": "Moscow",
            "description": "Test listing",
        }

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return RiskScoringOrchestrator()

    def test_initialization(self):
        """Test orchestrator initialization."""
        # Empty initialization
        orch = RiskScoringOrchestrator()
        assert len(orch.detection_plugins) == 0
        assert orch.min_confidence_threshold == 0.5

        # With plugins
        plugin = MockDetectionPlugin("test-plugin")
        orch = RiskScoringOrchestrator(detection_plugins=[plugin])
        assert len(orch.detection_plugins) == 1

        # Custom threshold
        orch = RiskScoringOrchestrator(min_confidence_threshold=0.7)
        assert orch.min_confidence_threshold == 0.7

    def test_register_plugin(self, orchestrator):
        """Test plugin registration."""
        plugin = MockDetectionPlugin("test-plugin")

        orchestrator.register_plugin(plugin)
        assert len(orchestrator.detection_plugins) == 1

        # Register same plugin again (should not duplicate)
        orchestrator.register_plugin(plugin)
        assert len(orchestrator.detection_plugins) == 1

    def test_unregister_plugin(self, orchestrator):
        """Test plugin unregistration."""
        plugin = MockDetectionPlugin("test-plugin")
        orchestrator.register_plugin(plugin)

        # Unregister existing plugin
        result = orchestrator.unregister_plugin("test-plugin")
        assert result is True
        assert len(orchestrator.detection_plugins) == 0

        # Unregister non-existent plugin
        result = orchestrator.unregister_plugin("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_run_with_no_plugins(self, orchestrator, sample_listing):
        """Test running with no registered plugins."""
        result = await orchestrator.run(sample_listing)

        assert isinstance(result, FraudScore)
        assert result.listing_id == "test-123"
        assert result.overall_score == 0.0
        assert result.confidence == 0.0
        assert result.risk_level == "safe"
        assert len(result.signals) == 0
        assert len(result.plugin_results) == 0

    @pytest.mark.asyncio
    async def test_run_with_single_plugin(self, orchestrator, sample_listing):
        """Test running with single detection plugin."""
        signals = [
            RiskSignal(
                signal_type="price_anomaly",
                score=0.8,
                confidence=0.9,
                reason="Price too low",
                metadata={"expected": 2000000, "actual": 1000000},
            )
        ]
        plugin = MockDetectionPlugin("price-detector", weight=1.0, score=0.8, signals=signals)
        orchestrator.register_plugin(plugin)

        result = await orchestrator.run(sample_listing)

        assert result.overall_score == 80.0  # 0.8 * 100
        assert result.risk_level == "fraud"  # 80 is >= 70
        assert len(result.signals) == 1
        assert len(result.plugin_results) == 1
        assert result.plugin_results[0].plugin_id == "price-detector"
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_run_with_multiple_plugins(self, orchestrator, sample_listing):
        """Test running with multiple detection plugins."""
        # Plugin 1: High risk (weight 0.6)
        plugin1 = MockDetectionPlugin(
            "price-detector",
            weight=0.6,
            score=0.9,
            signals=[
                RiskSignal(
                    signal_type="price_anomaly",
                    score=0.9,
                    confidence=0.95,
                    reason="Price too low",
                )
            ],
        )

        # Plugin 2: Low risk (weight 0.4)
        plugin2 = MockDetectionPlugin(
            "location-detector",
            weight=0.4,
            score=0.2,
            signals=[
                RiskSignal(
                    signal_type="location_ok",
                    score=0.2,
                    confidence=0.8,
                    reason="Location verified",
                )
            ],
        )

        orchestrator.register_plugin(plugin1)
        orchestrator.register_plugin(plugin2)

        result = await orchestrator.run(sample_listing)

        # Expected: (0.9 * 0.6 + 0.2 * 0.4) * 100 = 62.0
        assert abs(result.overall_score - 62.0) < 0.1
        assert result.risk_level == "suspicious"  # 62 is in [30, 70) range
        assert len(result.signals) == 2
        assert len(result.plugin_results) == 2

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, sample_listing):
        """Test that low confidence signals are filtered."""
        # High confidence signal
        high_conf_signal = RiskSignal(
            signal_type="high_confidence",
            score=0.8,
            confidence=0.9,
            reason="High confidence detection",
        )

        # Low confidence signal
        low_conf_signal = RiskSignal(
            signal_type="low_confidence",
            score=0.5,
            confidence=0.3,
            reason="Low confidence detection",
        )

        plugin = MockDetectionPlugin(
            "test-plugin",
            weight=1.0,
            score=0.65,
            signals=[high_conf_signal, low_conf_signal],
        )

        # Orchestrator with 0.5 threshold
        orchestrator = RiskScoringOrchestrator(detection_plugins=[plugin], min_confidence_threshold=0.5)

        result = await orchestrator.run(sample_listing)

        # Only high confidence signal should be included
        assert len(result.signals) == 1
        assert result.signals[0].signal_type == "high_confidence"

    @pytest.mark.asyncio
    async def test_plugin_error_handling(self, orchestrator, sample_listing):
        """Test that plugin errors don't crash orchestrator."""
        # Normal plugin
        good_plugin = MockDetectionPlugin("good-plugin", weight=0.5, score=0.5)

        # Failing plugin
        bad_plugin = MockDetectionPlugin("bad-plugin", weight=0.5, score=0.5)
        bad_plugin.analyze = AsyncMock(side_effect=Exception("Plugin error"))

        orchestrator.register_plugin(good_plugin)
        orchestrator.register_plugin(bad_plugin)

        result = await orchestrator.run(sample_listing)

        # Should get result from good plugin only
        assert len(result.plugin_results) == 1
        assert result.plugin_results[0].plugin_id == "good-plugin"

    def test_determine_risk_level(self, orchestrator):
        """Test risk level determination per ARCHITECTURE.md."""
        assert orchestrator._determine_risk_level(0.0) == "safe"
        assert orchestrator._determine_risk_level(10.0) == "safe"
        assert orchestrator._determine_risk_level(29.9) == "safe"
        assert orchestrator._determine_risk_level(30.0) == "suspicious"
        assert orchestrator._determine_risk_level(50.0) == "suspicious"
        assert orchestrator._determine_risk_level(69.9) == "suspicious"
        assert orchestrator._determine_risk_level(70.0) == "fraud"
        assert orchestrator._determine_risk_level(85.0) == "fraud"
        assert orchestrator._determine_risk_level(100.0) == "fraud"

    def test_compute_weighted_score_empty(self, orchestrator):
        """Test weighted score computation with no results."""
        score, confidence = orchestrator._compute_weighted_score([])
        assert score == 0.0
        assert confidence == 0.0

    def test_compute_weighted_score_equal_weights(self, orchestrator):
        """Test weighted score with equal weights."""
        plugin1 = MockDetectionPlugin("p1", weight=0.5, score=0.8)
        plugin2 = MockDetectionPlugin("p2", weight=0.5, score=0.4)

        orchestrator.register_plugin(plugin1)
        orchestrator.register_plugin(plugin2)

        results = [
            DetectionResult(
                plugin_id="p1",
                signals=[RiskSignal(signal_type="test", score=0.8, confidence=0.9, reason="test")],
                overall_score=0.8,
                processing_time_ms=10.0,
            ),
            DetectionResult(
                plugin_id="p2",
                signals=[RiskSignal(signal_type="test", score=0.4, confidence=0.7, reason="test")],
                overall_score=0.4,
                processing_time_ms=10.0,
            ),
        ]

        score, confidence = orchestrator._compute_weighted_score(results)

        # Expected: (0.8 * 0.5 + 0.4 * 0.5) * 100 = 60.0
        assert abs(score - 60.0) < 0.1
        assert 0.0 <= confidence <= 1.0

    def test_get_statistics(self, orchestrator):
        """Test getting orchestrator statistics."""
        plugin1 = MockDetectionPlugin("plugin1")
        plugin2 = MockDetectionPlugin("plugin2")

        orchestrator.register_plugin(plugin1)
        orchestrator.register_plugin(plugin2)

        stats = orchestrator.get_statistics()

        assert stats["plugins_registered"] == 2
        assert "plugin1" in stats["plugin_ids"]
        assert "plugin2" in stats["plugin_ids"]
        assert stats["min_confidence_threshold"] == 0.5

    @pytest.mark.asyncio
    async def test_metadata_collection(self, orchestrator, sample_listing):
        """Test that metadata is properly collected."""
        plugin = MockDetectionPlugin(
            "test-plugin",
            weight=1.0,
            score=0.7,
            signals=[
                RiskSignal(signal_type="test1", score=0.7, confidence=0.85, reason="test"),
                RiskSignal(signal_type="test2", score=0.6, confidence=0.90, reason="test"),
            ],
        )
        orchestrator.register_plugin(plugin)

        result = await orchestrator.run(sample_listing)

        assert "plugins_executed" in result.metadata
        assert result.metadata["plugins_executed"] == 1
        assert "total_signals" in result.metadata
        assert result.metadata["total_signals"] == 2
        assert "high_confidence_signals" in result.metadata
        assert "plugin_scores" in result.metadata
        assert len(result.metadata["plugin_scores"]) == 1

    @pytest.mark.asyncio
    async def test_processing_time_measured(self, orchestrator, sample_listing):
        """Test that processing time is measured."""
        plugin = MockDetectionPlugin("test-plugin")
        orchestrator.register_plugin(plugin)

        result = await orchestrator.run(sample_listing)

        assert result.processing_time_ms > 0.0
        assert result.processing_time_ms < 1000.0  # Should be fast


# Import asyncio for async tests
import asyncio
