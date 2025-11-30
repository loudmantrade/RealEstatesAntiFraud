from abc import ABC, abstractmethod
from typing import Dict


class ProcessingPlugin(ABC):
    """Abstract base class for processing plugins.

    Processing plugins transform and enrich listing data before storage
    or further processing.
    """

    @abstractmethod
    def get_metadata(self) -> Dict:
        pass

    @abstractmethod
    def process(self, listing: Dict) -> Dict:
        pass

    @abstractmethod
    def get_priority(self) -> int:
        return 10

    def shutdown(self) -> None:
        """
        Optional graceful shutdown hook for cleanup before reload.

        Override this method to:
        - Close connections
        - Stop background tasks
        - Release resources
        - Save state

        Default implementation does nothing.
        """
        pass
