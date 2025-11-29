"""Test processing plugin for integration testing."""

from typing import Any, Dict

from core.interfaces.processing_plugin import ProcessingPlugin


class TestProcessingPlugin(ProcessingPlugin):
    """Test processing plugin that normalizes prices and adds metadata.

    This plugin demonstrates a simple processing pipeline:
    1. Normalize price with configurable multiplier
    2. Add processing metadata
    3. Mark as processed
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the plugin with configuration.

        Args:
            config: Plugin configuration dictionary with:
                - price_multiplier: Float multiplier for price normalization (default: 1.0)
                - add_metadata: Boolean to add processing metadata (default: True)
        """
        self.config = config or {}
        self.price_multiplier = self.config.get("price_multiplier", 1.0)
        self.add_metadata = self.config.get("add_metadata", True)
        self.processed_count = 0

    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "id": "plugin-processing-test",
            "name": "Test Processing Plugin",
            "version": "1.0.0",
            "type": "processing",
            "description": "Test processing plugin for integration testing",
            "capabilities": ["price_normalization", "data_enrichment"],
            "processed_count": self.processed_count,
        }

    async def process(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Process a listing.

        Args:
            listing: Listing data dictionary

        Returns:
            Processed listing with normalized price and metadata
        """
        # Increment processing counter
        self.processed_count += 1

        # Create a copy to avoid modifying original
        processed = listing.copy()

        # Normalize price if present
        if "price" in processed and processed["price"] is not None:
            original_price = processed["price"]
            processed["price_normalized"] = original_price * self.price_multiplier

        # Add metadata if enabled
        if self.add_metadata:
            if "metadata" not in processed:
                processed["metadata"] = {}

            processed["metadata"]["processed_by"] = "plugin-processing-test"
            processed["metadata"]["processing_version"] = "1.0.0"
            processed["metadata"]["price_multiplier"] = self.price_multiplier

        # Mark as processed
        processed["processed"] = True

        return processed

    def get_weight(self) -> float:
        """Return plugin weight for prioritization."""
        return 1.0

    def get_priority(self) -> int:
        """Return plugin priority for execution order."""
        return 10

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        self.processed_count = 0
