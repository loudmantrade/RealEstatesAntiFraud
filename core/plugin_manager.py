from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from threading import RLock

from core.models.plugin import PluginMetadata
from core.validators.manifest import validate_manifest, ManifestValidationError


class PluginManager:
    """Simple in-memory plugin manager."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginMetadata] = {}
        self._lock = RLock()

    def register(self, metadata: PluginMetadata) -> PluginMetadata:
        """
        Register a plugin with the manager.
        
        Args:
            metadata: Plugin metadata to register
            
        Returns:
            Registered plugin metadata
        """
        with self._lock:
            if metadata.id in self._plugins:
                # Update metadata (version, description etc.)
                existing = self._plugins[metadata.id]
                for field, value in metadata.dict().items():
                    setattr(existing, field, value)
                return existing
            self._plugins[metadata.id] = metadata
            return metadata
    
    def register_from_manifest(self, manifest_path: Path) -> PluginMetadata:
        """
        Register a plugin from manifest file with validation.
        
        Args:
            manifest_path: Path to plugin.yaml file
            
        Returns:
            Registered plugin metadata
            
        Raises:
            ManifestValidationError: If manifest validation fails
            
        Example:
            >>> manager = PluginManager()
            >>> try:
            ...     plugin = manager.register_from_manifest(Path("plugin.yaml"))
            ...     print(f"Registered: {plugin.name}")
            ... except ManifestValidationError as e:
            ...     print(f"Failed: {e}")
        """
        # Validate manifest
        is_valid, errors = validate_manifest(manifest_path)
        if not is_valid:
            error_msg = f"Invalid manifest at {manifest_path}"
            raise ManifestValidationError(error_msg, errors)
        
        # Load and parse manifest
        import yaml
        with open(manifest_path) as f:
            manifest_data = yaml.safe_load(f)
        
        # Create metadata from manifest
        # For now, create basic PluginMetadata (will be extended later)
        metadata = PluginMetadata(
            id=manifest_data["id"],
            name=manifest_data["name"],
            version=manifest_data["version"],
            type=manifest_data["type"],
            enabled=True,  # Default enabled
            config=manifest_data.get("config", {})
        )
        
        return self.register(metadata)

    def list(self) -> List[PluginMetadata]:
        with self._lock:
            return list(self._plugins.values())

    def get(self, plugin_id: str) -> Optional[PluginMetadata]:
        with self._lock:
            return self._plugins.get(plugin_id)

    def enable(self, plugin_id: str) -> bool:
        with self._lock:
            plugin = self._plugins.get(plugin_id)
            if not plugin:
                return False
            plugin.enabled = True
            return True

    def disable(self, plugin_id: str) -> bool:
        with self._lock:
            plugin = self._plugins.get(plugin_id)
            if not plugin:
                return False
            plugin.enabled = False
            return True

    def remove(self, plugin_id: str) -> bool:
        with self._lock:
            return self._plugins.pop(plugin_id, None) is not None


# Singleton for simple usage
manager = PluginManager()
