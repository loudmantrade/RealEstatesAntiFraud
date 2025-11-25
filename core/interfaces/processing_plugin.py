from abc import ABC, abstractmethod
from typing import Dict


class ProcessingPlugin(ABC):
    @abstractmethod
    def get_metadata(self) -> Dict:
        pass

    @abstractmethod
    def process(self, listing: Dict) -> Dict:
        pass

    @abstractmethod
    def get_priority(self) -> int:
        return 10
