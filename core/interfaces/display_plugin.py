from abc import ABC, abstractmethod
from typing import Dict


class DisplayPlugin(ABC):
    @abstractmethod
    def format_listing(self, listing: Dict, format: str) -> Dict:
        pass

    @abstractmethod
    def get_template(self) -> str:
        return "default"

    def shutdown(self) -> None:
        """
        Optional graceful shutdown hook for cleanup before reload.
        
        Override this method to release resources.
        Default implementation does nothing.
        """
        pass
