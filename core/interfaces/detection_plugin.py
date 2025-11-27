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

    def shutdown(self) -> None:
        """
        Optional graceful shutdown hook for cleanup before reload.

        Override this method to release resources and save state.
        Default implementation does nothing.
        """
        pass
