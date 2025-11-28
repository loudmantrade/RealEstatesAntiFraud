"""Test processing plugin in nested directory."""

from typing import Dict

from core.interfaces.processing_plugin import ProcessingPlugin


class NestedProcessingPlugin(ProcessingPlugin):
    """Test processing plugin."""

    def __init__(self):
        self.initialized = True

    def get_metadata(self) -> Dict:
        """Return plugin metadata."""
        return {"name": "Nested Processing Plugin", "version": "1.0.0"}

    def process(self, listing: Dict) -> Dict:
        """Process listing data."""
        listing["processed"] = True
        return listing

    def get_priority(self) -> int:
        """Return processing priority."""
        return 10
