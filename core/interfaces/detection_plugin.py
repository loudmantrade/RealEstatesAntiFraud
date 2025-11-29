from abc import ABC, abstractmethod
from typing import Dict, List

from pydantic import BaseModel, Field


class RiskSignal(BaseModel):
    """Risk signal detected by a fraud detection plugin.

    Attributes:
        signal_type: Type of risk detected (e.g., 'price_anomaly', 'duplicate_listing')
        score: Risk score from 0.0 (no risk) to 1.0 (high risk)
        confidence: Confidence level from 0.0 to 1.0
        reason: Human-readable explanation
        metadata: Additional context about the signal
    """

    signal_type: str
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    metadata: Dict = Field(default_factory=dict)


class DetectionResult(BaseModel):
    """Result from a detection plugin analysis.

    Attributes:
        plugin_id: ID of the plugin that generated this result
        signals: List of risk signals detected
        overall_score: Aggregated risk score from this plugin (0.0 to 1.0)
        processing_time_ms: Time taken to analyze in milliseconds
    """

    plugin_id: str
    signals: List[RiskSignal] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float = Field(ge=0.0)


class DetectionPlugin(ABC):
    """Abstract base class for fraud detection plugins.

    Detection plugins analyze listings for fraud indicators and return
    risk signals with confidence scores.
    """

    @abstractmethod
    def get_metadata(self) -> Dict:
        """Get plugin metadata.

        Returns:
            Dict with keys: id, name, version, description
        """
        pass

    @abstractmethod
    async def analyze(self, listing: Dict) -> DetectionResult:
        """Analyze listing for fraud indicators.

        Args:
            listing: Listing data to analyze

        Returns:
            DetectionResult with signals and scores
        """
        pass

    @abstractmethod
    def get_weight(self) -> float:
        """Get plugin weight for score aggregation.

        Returns:
            Weight value between 0.0 and 1.0
        """
        return 0.1

    def shutdown(self) -> None:
        """Optional graceful shutdown hook for cleanup before reload.

        Override this method to release resources and save state.
        Default implementation does nothing.
        """
        pass
