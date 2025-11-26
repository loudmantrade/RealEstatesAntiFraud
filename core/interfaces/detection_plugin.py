from abc import ABC, abstractmethod
from typing import Dict


class DetectionPlugin(ABC):
    @abstractmethod
    def get_metadata(self) -> Dict:
        pass

    @abstractmethod
    def analyze(self, listing: Dict) -> Dict:
        """Return signals and confidence."""
        pass

    @abstractmethod
    def get_weight(self) -> float:
        return 0.1
