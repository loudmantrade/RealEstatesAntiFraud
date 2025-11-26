from typing import List, Optional
from pydantic import BaseModel, Field


class PluginMetadata(BaseModel):
    id: str = Field(..., description="Unique plugin ID")
    name: str
    version: str
    type: str  # source | processing | detection | search | display
    description: Optional[str] = None
    author: Optional[str] = None
    capabilities: List[str] = []
    enabled: bool = False


class PluginRegistrationRequest(BaseModel):
    metadata: PluginMetadata
    # Optional: path or uri to plugin package
    package_path: Optional[str] = None
