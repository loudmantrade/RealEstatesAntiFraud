"""Test source plugin for unit testing."""
from core.interfaces.source_plugin import SourcePlugin


class CianSourcePlugin(SourcePlugin):
    """Test implementation of source plugin."""
    
    def __init__(self):
        self.initialized = True
    
    def fetch(self, params: dict) -> list:
        """Fetch listings from source."""
        return [{"id": "test-1", "title": "Test Listing"}]
    
    def validate_config(self, config: dict) -> bool:
        """Validate plugin configuration."""
        return True
