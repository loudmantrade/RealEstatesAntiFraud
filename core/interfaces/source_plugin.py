from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Iterator, Optional


class SourcePlugin(ABC):
    """Base class for all source plugins."""

    @abstractmethod
    def get_metadata(self) -> Dict:
        pass

    @abstractmethod
    def configure(self, config: Dict) -> None:
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        pass

    @abstractmethod
    def scrape(self, params: Dict) -> Iterator[Dict]:
        """Yield listings in UDM format."""
        pass

    @abstractmethod
    def scrape_single(self, listing_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def validate_listing(self, listing: Dict) -> bool:
        pass

    @abstractmethod
    def get_statistics(self) -> Dict:
        pass

    def shutdown(self) -> None:
        """
        Optional graceful shutdown hook for cleanup before reload.
        
        Override this method to:
        - Close database connections
        - Stop background tasks
        - Release resources
        - Save state
        
        Default implementation does nothing.
        """
        pass
