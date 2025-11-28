from abc import ABC, abstractmethod
from typing import Dict, List


class SearchPlugin(ABC):
    @abstractmethod
    def index(self, listing: Dict) -> bool:
        pass

    @abstractmethod
    def search(self, query: Dict) -> List[Dict]:
        pass

    @abstractmethod
    def suggest(self, prefix: str) -> List[str]:
        return []

    def shutdown(self) -> None:
        """
        Optional graceful shutdown hook for cleanup before reload.

        Override this method to close search index connections and
        release resources. Default implementation does nothing.
        """
        pass
