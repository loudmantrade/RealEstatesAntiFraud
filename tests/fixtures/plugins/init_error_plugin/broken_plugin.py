"""Plugin that raises error during initialization."""

from typing import Dict, Iterator, Optional

from core.interfaces.source_plugin import SourcePlugin


class BrokenPlugin(SourcePlugin):
    """Plugin that fails to initialize."""

    def __init__(self):
        raise RuntimeError("Initialization failed intentionally for testing")

    def get_metadata(self) -> Dict:
        return {}

    def configure(self, config: Dict) -> None:
        pass

    def validate_config(self) -> bool:
        return True

    def scrape(self, params: Dict) -> Iterator[Dict]:
        yield from []

    def scrape_single(self, listing_id: str) -> Optional[Dict]:
        return None

    def validate_listing(self, listing: Dict) -> bool:
        return False

    def get_statistics(self) -> Dict:
        return {}
