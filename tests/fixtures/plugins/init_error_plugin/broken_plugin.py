"""Plugin that raises error during initialization."""
from core.interfaces.source_plugin import SourcePlugin


class BrokenPlugin(SourcePlugin):
    """Plugin that fails to initialize."""
    
    def __init__(self):
        raise RuntimeError("Initialization failed intentionally for testing")
    
    def fetch(self, params: dict) -> list:
        return []
    
    def validate_config(self, config: dict) -> bool:
        return True
