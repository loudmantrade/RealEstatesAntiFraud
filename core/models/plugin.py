from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PluginAuthor(BaseModel):
    """Plugin author information"""

    name: str
    email: Optional[str] = None
    url: Optional[str] = None


class PluginMetadata(BaseModel):
    id: str = Field(..., description="Unique plugin ID")
    name: str
    version: str
    type: str  # source | processing | detection | search | display
    description: Optional[str] = None
    author: Optional[PluginAuthor] = None
    capabilities: List[str] = []
    enabled: bool = False
    dependencies: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Plugin dependencies with version constraints (plugin_id -> constraint)",
    )
    weight: Optional[float] = Field(
        default=None,
        description="Plugin weight for detection scoring (0.0-1.0). If None, uses plugin's get_weight() method",
    )


class PluginRegistrationRequest(BaseModel):
    metadata: PluginMetadata
    # Optional: path or uri to plugin package
    package_path: Optional[str] = None
