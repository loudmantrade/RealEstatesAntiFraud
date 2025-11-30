"""Test dependent plugin for integration testing."""

from typing import Any, Dict

from core.interfaces.processing_plugin import ProcessingPlugin


class TestDependentPlugin(ProcessingPlugin):
    """Test plugin that depends on other plugins.

    This plugin demonstrates dependency management:
    1. Depends on processing and detection plugins
    2. Uses normalized data from processing plugin
    3. Adds enriched metadata
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the plugin with configuration.

        Args:
            config: Plugin configuration dictionary with:
                - use_normalization: Boolean to use normalized prices (default: True)
        """
        self.config = config or {}
        self.use_normalization = self.config.get("use_normalization", True)
        self.processed_count = 0

    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "id": "plugin-dependent-test",
            "name": "Test Dependent Plugin",
            "version": "1.0.0",
            "type": "processing",
            "description": "Test plugin that depends on other plugins",
            "capabilities": ["enriched_processing", "dependent_processing"],
            "dependencies": ["plugin-processing-test", "plugin-detection-test"],
            "processed_count": self.processed_count,
        }

    async def process(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Process a listing with dependency on other plugins.

        Args:
            listing: Listing data dictionary (potentially already processed)

        Returns:
            Enriched listing with dependent processing metadata
        """
        self.processed_count += 1

        # Create a copy to avoid modifying original
        processed = listing.copy()

        # Use normalized price if available (from processing plugin)
        if self.use_normalization and "price_normalized" in processed:
            processed["price_final"] = processed["price_normalized"]
        elif "price" in processed:
            processed["price_final"] = processed["price"]

        # Add enriched metadata
        if "metadata" not in processed:
            processed["metadata"] = {}

        processed["metadata"]["enriched_by"] = "plugin-dependent-test"
        processed["metadata"]["enrichment_version"] = "1.0.0"
        processed["metadata"]["used_normalization"] = self.use_normalization and "price_normalized" in listing

        # Mark as enriched
        processed["enriched"] = True

        return processed

    def get_weight(self) -> float:
        """Return plugin weight for prioritization."""
        return 0.8

    def get_priority(self) -> int:
        """Return plugin priority for execution order."""
        return 20  # Higher priority since it depends on others

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        self.processed_count = 0
