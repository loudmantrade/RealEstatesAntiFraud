"""Test processing plugin in nested directory."""
from core.interfaces.processing_plugin import ProcessingPlugin


class ProcessingPlugin(ProcessingPlugin):
    """Test processing plugin."""
    
    def __init__(self):
        self.initialized = True
    
    def process(self, data: dict) -> dict:
        """Process listing data."""
        data["processed"] = True
        return data
    
    def validate_config(self, config: dict) -> bool:
        """Validate configuration."""
        return True
