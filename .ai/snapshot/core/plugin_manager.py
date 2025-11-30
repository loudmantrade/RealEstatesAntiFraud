from __future__ import annotations
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from threading import RLock

from core.models.plugin import PluginMetadata
from core.validators.manifest import validate_manifest, ManifestValidationError
from core.dependency_graph import (
    DependencyGraph,
    CyclicDependencyError,
    MissingDependencyError
)

logger = logging.getLogger(__name__)


class PluginManager:
    """Simple in-memory plugin manager."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginMetadata] = {}
        self._instances: Dict[str, any] = {}  # Store plugin instances
        self._modules: Dict[str, any] = {}  # Store imported modules for reload
        self._dependency_graph = DependencyGraph()  # Manage plugin dependencies
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
            removed = self._plugins.pop(plugin_id, None) is not None
            if removed and self._dependency_graph.has_plugin(plugin_id):
                self._dependency_graph.remove_plugin(plugin_id)
            return removed

    def build_dependency_graph(self) -> None:
        """
        Build dependency graph from registered plugins.

        Parses plugin dependencies and constructs DAG for load order determination.
        Must be called before load_plugins() if plugins have dependencies.

        Raises:
            MissingDependencyError: If plugin depends on unregistered plugin
            CyclicDependencyError: If circular dependencies detected

        Example:
            >>> manager = PluginManager()
            >>> # Register plugins with dependencies...
            >>> try:
            ...     manager.build_dependency_graph()
            ...     print("Dependency graph built successfully")
            ... except CyclicDependencyError as e:
            ...     print(f"Circular dependency: {e.cycle}")
        """
        with self._lock:
            # Clear existing graph
            self._dependency_graph = DependencyGraph()

            # Add all plugins to graph
            # First pass: add all nodes without dependencies
            for plugin_id, metadata in self._plugins.items():
                # Dependencies will be parsed from config/manifest
                # For now, we'll extract from metadata.config if present
                deps = []
                if hasattr(metadata, 'dependencies') and metadata.dependencies:
                    deps = metadata.dependencies
                elif isinstance(metadata.config, dict):
                    # Check if dependencies stored in config
                    deps = metadata.config.get('dependencies', [])

                self._dependency_graph.add_plugin(
                    plugin_id=plugin_id,
                    version=metadata.version,
                    dependencies=deps
                )
                logger.debug(
                    f"Added {plugin_id} to graph with {len(deps)} dependencies"
                )

            # Build and validate graph
            try:
                self._dependency_graph.build()
                logger.info(
                    f"Dependency graph built successfully with "
                    f"{len(self._dependency_graph)} plugins"
                )
            except MissingDependencyError as e:
                logger.error(f"Missing dependencies: {e}")
                raise
            except CyclicDependencyError as e:
                logger.error(f"Circular dependencies detected: {e.cycle}")
                raise

    def get_load_order(self) -> List[str]:
        """
        Get plugin load order based on dependency graph.

        Returns:
            List of plugin IDs in topological order (dependencies first)

        Raises:
            RuntimeError: If dependency graph not built

        Example:
            >>> manager = PluginManager()
            >>> manager.build_dependency_graph()
            >>> order = manager.get_load_order()
            >>> print(f"Load order: {' -> '.join(order)}")
        """
        with self._lock:
            return self._dependency_graph.get_load_order()

    def reload_plugin(self, plugin_id: str) -> PluginMetadata:
        """
        Hot reload a plugin without restarting the service.

        Process:
        1. Check plugin exists and has instance
        2. Call shutdown() on old instance for graceful cleanup
        3. Reload Python module using importlib.reload()
        4. Create new instance with updated code
        5. Replace old instance with new one
        6. Update metadata if manifest changed

        Args:
            plugin_id: ID of plugin to reload

        Returns:
            Updated plugin metadata after reload

        Raises:
            ValueError: If plugin not found or not loaded
            RuntimeError: If reload fails

        Example:
            >>> manager = PluginManager()
            >>> # After modifying plugin code...
            >>> updated = manager.reload_plugin("plugin-source-cian")
            >>> print(f"Reloaded: {updated.name} v{updated.version}")
        """
        with self._lock:
            # Check plugin exists
            metadata = self._plugins.get(plugin_id)
            if not metadata:
                raise ValueError(f"Plugin '{plugin_id}' not found")

            # Check plugin has instance (was loaded)
            old_instance = self._instances.get(plugin_id)
            if not old_instance:
                raise ValueError(
                    f"Plugin '{plugin_id}' not loaded, cannot reload. "
                    "Use load_plugins() first."
                )

            # Get stored module reference
            old_module = self._modules.get(plugin_id)
            if not old_module:
                raise RuntimeError(
                    f"Plugin '{plugin_id}' has no module reference. "
                    "Cannot reload."
                )

            logger.info(f"Starting hot reload for plugin: {plugin_id}")

            try:
                # Step 1: Graceful shutdown of old instance
                if hasattr(old_instance, 'shutdown'):
                    try:
                        logger.debug(f"Calling shutdown() on {plugin_id}")
                        old_instance.shutdown()
                        logger.info(f"Graceful shutdown completed for {plugin_id}")
                    except Exception as e:
                        logger.warning(
                            f"Error during shutdown of {plugin_id}: {e}. "
                            "Continuing with reload...",
                            exc_info=True
                        )

                # Step 2: Reload Python module to get updated code
                try:
                    module_name = getattr(old_module, '__name__', 'unknown')
                    logger.debug(f"Reloading module: {module_name}")
                    reloaded_module = importlib.reload(old_module)
                    logger.debug(f"Module reloaded successfully")
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to reload module for {plugin_id}: {e}"
                    ) from e

                # Step 3: Find manifest to re-validate and get entrypoint
                # For now, we need to find the manifest path
                # TODO: Store manifest path in metadata for easier reload
                # As a workaround, we'll use the stored module to get class

                # Get updated class from reloaded module
                plugin_class_name = type(old_instance).__name__
                if not hasattr(reloaded_module, plugin_class_name):
                    raise RuntimeError(
                        f"Class '{plugin_class_name}' not found in reloaded module"
                    )

                updated_plugin_class = getattr(reloaded_module, plugin_class_name)

                # Step 4: Create new instance
                try:
                    new_instance = updated_plugin_class()
                    logger.info(f"New instance created for {plugin_id}")
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to instantiate new plugin instance: {e}"
                    ) from e

                # Step 5: Replace old instance with new one
                self._instances[plugin_id] = new_instance
                self._modules[plugin_id] = reloaded_module

                logger.info(f"Hot reload completed successfully for {plugin_id}")

                # Return updated metadata
                # Note: metadata version stays same unless manifest changed
                return metadata

            except Exception as e:
                # On any error, try to restore old instance if possible
                logger.error(
                    f"Hot reload failed for {plugin_id}: {e}. "
                    "Old instance may still be functional.",
                    exc_info=True
                )
                raise RuntimeError(
                    f"Hot reload failed for {plugin_id}: {e}"
                ) from e

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
            ... (file continues)
