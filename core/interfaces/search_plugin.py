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
