"""Test source plugin for unit testing."""

from typing import Dict, Iterator, Optional

from core.interfaces.source_plugin import SourcePlugin


class CianSourcePlugin(SourcePlugin):
    """Test implementation of source plugin."""

    def __init__(self):
        self.initialized = True
        self._config = {}

    def get_metadata(self) -> Dict:
        """Return plugin metadata."""
        return {"name": "Test Cian Plugin", "version": "1.0.0"}

    def configure(self, config: Dict) -> None:
        """Configure the plugin."""
        self._config = config

    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        return True

    def scrape(self, params: Dict) -> Iterator[Dict]:
        """Yield listings from source."""
        yield {"id": "test-1", "title": "Test Listing"}

    def scrape_single(self, listing_id: str) -> Optional[Dict]:
        """Fetch a single listing by ID."""
        if listing_id == "test-1":
            return {"id": "test-1", "title": "Test Listing"}
        return None

    def validate_listing(self, listing: Dict) -> bool:
        """Validate listing data."""
        return "id" in listing and "title" in listing

    def get_statistics(self) -> Dict:
        """Return plugin statistics."""
        return {"listings_scraped": 1}
