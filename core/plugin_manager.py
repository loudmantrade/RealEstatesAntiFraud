from __future__ import annotations
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from threading import RLock

from core.models.plugin import PluginMetadata
from core.validators.manifest import validate_manifest, ManifestValidationError

logger = logging.getLogger(__name__)


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
    
    def discover_plugins(self, plugins_dir: Path) -> List[Path]:
        """
        Recursively discover plugin manifests in plugins directory.
        
        Scans the directory tree looking for plugin.yaml files and validates them.
        Returns paths to valid manifests only; logs errors for invalid ones.
        
        Args:
            plugins_dir: Root directory to scan for plugins
            
        Returns:
            List of paths to valid plugin.yaml files
            
        Example:
            >>> manager = PluginManager()
            >>> manifests = manager.discover_plugins(Path("plugins"))
            >>> print(f"Found {len(manifests)} valid plugins")
        """
        if not plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {plugins_dir}")
            return []
        
        if not plugins_dir.is_dir():
            logger.error(f"Plugins path is not a directory: {plugins_dir}")
            return []
        
        discovered = []
        
        # Find all plugin.yaml files recursively
        for manifest_path in plugins_dir.rglob("plugin.yaml"):
            logger.debug(f"Found manifest: {manifest_path}")
            
            # Validate manifest
            is_valid, errors = validate_manifest(manifest_path)
            if not is_valid:
                logger.error(
                    f"Invalid manifest at {manifest_path}:\n" +
                    "\n".join(f"  - {err}" for err in errors)
                )
                continue
            
            discovered.append(manifest_path)
            logger.info(f"Discovered valid plugin: {manifest_path}")
        
        logger.info(f"Discovery complete: {len(discovered)} valid plugins found")
        return discovered
    
    def load_plugins(
        self, 
        manifest_paths: Optional[List[Path]] = None,
        plugins_dir: Optional[Path] = None
    ) -> Tuple[List[PluginMetadata], List[Tuple[Path, Exception]]]:
        """
        Load plugins from manifests and instantiate their classes.
        
        Can either load from provided manifest paths or auto-discover from directory.
        For each manifest:
        1. Validates and registers metadata via register_from_manifest()
        2. Dynamically imports the Python module specified in entrypoint
        3. Instantiates the plugin class
        4. Stores instance for future use
        
        Args:
            manifest_paths: Optional list of manifest paths to load
            plugins_dir: Optional directory to discover plugins from
            
        Returns:
            Tuple of (successful_plugins, failed_plugins)
            - successful_plugins: List of loaded plugin metadata
            - failed_plugins: List of (manifest_path, exception) tuples
            
        Raises:
            ValueError: If neither manifest_paths nor plugins_dir provided
            
        Example:
            >>> manager = PluginManager()
            >>> loaded, failed = manager.load_plugins(plugins_dir=Path("plugins"))
            >>> print(f"Loaded: {len(loaded)}, Failed: {len(failed)}")
        """
        # Determine which manifests to load
        if manifest_paths is None:
            if plugins_dir is None:
                raise ValueError("Either manifest_paths or plugins_dir must be provided")
            manifest_paths = self.discover_plugins(plugins_dir)
        
        loaded: List[PluginMetadata] = []
        failed: List[Tuple[Path, Exception]] = []
        
        for manifest_path in manifest_paths:
            try:
                # Register plugin metadata
                metadata = self.register_from_manifest(manifest_path)
                logger.info(f"Registered plugin: {metadata.id} v{metadata.version}")
                
                # Load manifest to get entrypoint
                import yaml
                with open(manifest_path) as f:
                    manifest_data = yaml.safe_load(f)
                
                # Check if entrypoint is specified
                entrypoint = manifest_data.get("entrypoint")
                if not entrypoint:
                    logger.warning(
                        f"Plugin {metadata.id} has no entrypoint, skipping instantiation"
                    )
                    loaded.append(metadata)
                    continue
                
                # Parse entrypoint object: {"module": "...", "class": "..."}
                if not isinstance(entrypoint, dict):
                    raise ValueError(
                        f"Invalid entrypoint format '{entrypoint}', "
                        "expected object with 'module' and 'class' fields"
                    )
                
                module_path = entrypoint.get("module")
                class_name = entrypoint.get("class")
                
                if not module_path or not class_name:
                    raise ValueError(
                        f"Entrypoint must have both 'module' and 'class' fields"
                    )
                
                # Add plugin directory to sys.path for imports
                plugin_dir = manifest_path.parent
                if str(plugin_dir) not in sys.path:
                    sys.path.insert(0, str(plugin_dir))
                
                # Ensure project root is in sys.path for core imports
                # Find project root (directory containing core/)
                project_root = Path(__file__).parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                try:
                    # Dynamically import module
                    module = importlib.import_module(module_path)
                    logger.debug(f"Imported module: {module_path}")
                    
                    # Get plugin class
                    if not hasattr(module, class_name):
                        raise AttributeError(
                            f"Module '{module_path}' has no class '{class_name}'"
                        )
                    
                    plugin_class = getattr(module, class_name)
                    logger.debug(f"Found class: {class_name}")
                    
                    # Instantiate plugin
                    # TODO: Pass configuration and dependencies when available
                    plugin_instance = plugin_class()
                    logger.info(f"Instantiated plugin: {metadata.id}")
                    
                    # Store instance reference (extend PluginMetadata later)
                    # For now, just mark as successfully loaded
                    loaded.append(metadata)
                    
                except (ImportError, AttributeError, TypeError) as e:
                    logger.error(
                        f"Failed to instantiate plugin {metadata.id}: {e}",
                        exc_info=True
                    )
                    failed.append((manifest_path, e))
                    # Remove from registered plugins since instantiation failed
                    self.remove(metadata.id)
                    
            except ManifestValidationError as e:
                logger.error(f"Manifest validation failed for {manifest_path}: {e}")
                failed.append((manifest_path, e))
                
            except Exception as e:
                logger.error(
                    f"Unexpected error loading plugin from {manifest_path}: {e}",
                    exc_info=True
                )
                failed.append((manifest_path, e))
        
        logger.info(
            f"Plugin loading complete: {len(loaded)} successful, {len(failed)} failed"
        )
        return loaded, failed


# Singleton for simple usage
manager = PluginManager()
