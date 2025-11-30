from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from core.dependency_graph import CyclicDependencyError, DependencyGraph, MissingDependencyError
from core.models.plugin import PluginMetadata
from core.validators.manifest import ManifestValidationError, validate_manifest

logger = logging.getLogger(__name__)


class PluginManager:
    """Simple in-memory plugin manager."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginMetadata] = {}
        self._instances: Dict[str, Any] = {}  # Store plugin instances
        self._modules: Dict[str, Any] = {}  # Store imported modules for reload
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
        # Extract dependencies in correct format
        deps_config = manifest_data.get("dependencies", {})
        plugin_deps = {}

        # Support both formats:
        # 1. {"plugin-a": "^1.0.0", "plugin-b": "~2.0.0"}  (direct dict)
        # 2. {"plugins": {"plugin-a": "^1.0.0"}}  (nested dict)
        if isinstance(deps_config, dict):
            if "plugins" in deps_config:
                plugin_deps = deps_config.get("plugins", {})
            else:
                # Assume it's direct mapping if no 'plugins' key
                plugin_deps = deps_config

        # Parse author field if present
        author_data = manifest_data.get("author")
        from core.models.plugin import PluginAuthor

        author = None
        if author_data:
            if isinstance(author_data, dict):
                author = PluginAuthor(**author_data)
            elif isinstance(author_data, str):
                # Legacy support: treat string as name
                author = PluginAuthor(name=author_data)

        metadata = PluginMetadata(
            id=manifest_data["id"],
            name=manifest_data["name"],
            version=manifest_data["version"],
            type=manifest_data["type"],
            enabled=True,  # Default enabled
            description=manifest_data.get("description"),
            author=author,
            capabilities=manifest_data.get("capabilities", []),
            dependencies=plugin_deps,
        )

        return self.register(metadata)

    def list(self) -> List[PluginMetadata]:
        with self._lock:
            return list(self._plugins.values())

    def get(self, plugin_id: str) -> Optional[PluginMetadata]:
        with self._lock:
            return self._plugins.get(plugin_id)

    def get_by_type(self, plugin_type: str, enabled_only: bool = True) -> List[PluginMetadata]:
        """
        Get all plugins of specific type.

        Args:
            plugin_type: Plugin type to filter by (e.g., 'detection', 'source')
            enabled_only: If True, return only enabled plugins

        Returns:
            List of plugin metadata matching the type

        Example:
            >>> manager = PluginManager()
            >>> detection_plugins = manager.get_by_type('detection', enabled_only=True)
            >>> print(f"Active detection plugins: {len(detection_plugins)}")
        """
        with self._lock:
            plugins = [p for p in self._plugins.values() if p.type == plugin_type]
            if enabled_only:
                plugins = [p for p in plugins if p.enabled]
            return plugins

    def get_instance(self, plugin_id: str) -> Optional[Any]:
        """
        Get loaded plugin instance.

        Args:
            plugin_id: ID of plugin to get instance for

        Returns:
            Plugin instance if loaded, None otherwise

        Example:
            >>> manager = PluginManager()
            >>> instance = manager.get_instance('plugin-detection-price')
            >>> if instance:
            ...     result = instance.analyze(listing)
        """
        with self._lock:
            return self._instances.get(plugin_id)

    def get_detection_plugins(self, enabled_only: bool = True, wrap_with_config: bool = True) -> List[Any]:
        """
        Get all loaded detection plugin instances.

        Args:
            enabled_only: If True, return only enabled plugins
            wrap_with_config: If True, wraps plugins with DetectionPluginWrapper
                             to apply configured weights

        Returns:
            List of detection plugin instances (wrapped or unwrapped)

        Example:
            >>> manager = PluginManager()
            >>> plugins = manager.get_detection_plugins()
            >>> orchestrator = RiskScoringOrchestrator(detection_plugins=plugins)
        """
        with self._lock:
            detection_metadata = self.get_by_type("detection", enabled_only=enabled_only)
            instances = []

            for metadata in detection_metadata:
                instance = self._instances.get(metadata.id)
                if not instance:
                    logger.warning(f"Detection plugin {metadata.id} registered but not loaded")
                    continue

                if wrap_with_config:
                    # Wrap plugin with configured weight override
                    from core.fraud.detection_plugin_wrapper import DetectionPluginWrapper

                    wrapped = DetectionPluginWrapper(
                        plugin=instance,
                        plugin_id=metadata.id,
                        weight_override=metadata.weight,
                    )
                    instances.append(wrapped)
                else:
                    instances.append(instance)

            return instances

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

    def set_weight(self, plugin_id: str, weight: float) -> bool:
        """
        Set custom weight for detection plugin.

        Args:
            plugin_id: ID of plugin to set weight for
            weight: Weight value (0.0-1.0)

        Returns:
            True if weight set successfully, False if plugin not found

        Raises:
            ValueError: If weight is not in valid range

        Example:
            >>> manager = PluginManager()
            >>> manager.set_weight('plugin-detection-price', 0.8)
        """
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")

        with self._lock:
            plugin = self._plugins.get(plugin_id)
            if not plugin:
                return False
            plugin.weight = weight
            logger.info(f"Set weight {weight} for plugin {plugin_id}")
            return True

    def get_weight(self, plugin_id: str) -> Optional[float]:
        """
        Get configured weight for detection plugin.

        If weight not set in metadata, returns None (will use plugin's get_weight() method).

        Args:
            plugin_id: ID of plugin to get weight for

        Returns:
            Configured weight or None

        Example:
            >>> manager = PluginManager()
            >>> weight = manager.get_weight('plugin-detection-price')
            >>> if weight is None:
            ...     # Will use plugin's default weight
        """
        with self._lock:
            plugin = self._plugins.get(plugin_id)
            if not plugin:
                return None
            return plugin.weight

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

            # Add all plugins to graph with their version constraints
            for plugin_id, metadata in self._plugins.items():
                # Extract dependencies from metadata
                # Dependencies should be Dict[str, str] mapping plugin_id -> version_constraint
                deps = metadata.dependencies or {}

                # If dependencies is a list (old format), convert to dict with "*" wildcard
                if isinstance(deps, list):
                    deps = {dep_id: "*" for dep_id in deps}

                self._dependency_graph.add_plugin(plugin_id=plugin_id, version=metadata.version, dependencies=deps)
                logger.debug(f"Added {plugin_id} to graph with {len(deps)} dependencies")

            # Build and validate graph
            try:
                self._dependency_graph.build()
                logger.info(f"Dependency graph built successfully with " f"{len(self._dependency_graph)} plugins")
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
                raise ValueError(f"Plugin '{plugin_id}' not loaded, cannot reload. " "Use load_plugins() first.")

            # Get stored module reference
            old_module = self._modules.get(plugin_id)
            if not old_module:
                raise RuntimeError(f"Plugin '{plugin_id}' has no module reference. " "Cannot reload.")

            logger.info(f"Starting hot reload for plugin: {plugin_id}")

            try:
                # Step 1: Graceful shutdown of old instance
                if hasattr(old_instance, "shutdown"):
                    try:
                        logger.debug(f"Calling shutdown() on {plugin_id}")
                        old_instance.shutdown()
                        logger.info(f"Graceful shutdown completed for {plugin_id}")
                    except Exception as e:
                        logger.warning(
                            f"Error during shutdown of {plugin_id}: {e}. " "Continuing with reload...",
                            exc_info=True,
                        )

                # Step 2: Reload Python module to get updated code
                try:
                    import importlib
                    import sys

                    module_name = getattr(old_module, "__name__", "unknown")
                    logger.debug(f"Reloading module: {module_name}")

                    # Ensure module is in sys.modules for reload
                    if module_name not in sys.modules:
                        logger.debug(f"Module {module_name} not in sys.modules, re-adding it")
                        sys.modules[module_name] = old_module

                    # Use standard reload
                    reloaded_module = importlib.reload(old_module)
                    logger.debug("Module reloaded successfully")
                except Exception as e:
                    raise RuntimeError(f"Failed to reload module for {plugin_id}: {e}") from e

                # Step 3: Find manifest to re-validate and get entrypoint
                # For now, we need to find the manifest path
                # TODO: Store manifest path in metadata for easier reload
                # As a workaround, we'll use the stored module to get class

                # Get updated class from reloaded module
                plugin_class_name = type(old_instance).__name__
                if not hasattr(reloaded_module, plugin_class_name):
                    raise RuntimeError(f"Class '{plugin_class_name}' not found in reloaded module")

                updated_plugin_class = getattr(reloaded_module, plugin_class_name)

                # Step 4: Create new instance
                try:
                    new_instance = updated_plugin_class()
                    logger.info(f"New instance created for {plugin_id}")
                except Exception as e:
                    raise RuntimeError(f"Failed to instantiate new plugin instance: {e}") from e

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
                    f"Hot reload failed for {plugin_id}: {e}. " "Old instance may still be functional.",
                    exc_info=True,
                )
                raise RuntimeError(f"Hot reload failed for {plugin_id}: {e}") from e

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
                logger.error(f"Invalid manifest at {manifest_path}:\n" + "\n".join(f"  - {err}" for err in errors))
                continue

            discovered.append(manifest_path)
            logger.info(f"Discovered valid plugin: {manifest_path}")

        logger.info(f"Discovery complete: {len(discovered)} valid plugins found")
        return discovered

    def load_plugins(
        self,
        manifest_paths: Optional[List[Path]] = None,
        plugins_dir: Optional[Path] = None,
    ) -> Tuple[List[PluginMetadata], List[Tuple[Path, Exception]]]:
        """
        Load plugins from manifests and instantiate their classes.

        Can either load from provided manifest paths or auto-discover from directory.
        For each manifest:
        1. Validates and registers metadata via register_from_manifest()
        2. Parses dependencies from manifest
        3. Builds dependency graph and determines load order
        4. Dynamically imports Python modules in topological order
        5. Instantiates plugin classes
        6. Stores instances for future use

        Args:
            manifest_paths: Optional list of manifest paths to load
            plugins_dir: Optional directory to discover plugins from

        Returns:
            Tuple of (successful_plugins, failed_plugins)
            - successful_plugins: List of loaded plugin metadata
            - failed_plugins: List of (manifest_path, exception) tuples

        Raises:
            ValueError: If neither manifest_paths nor plugins_dir provided
            CyclicDependencyError: If circular dependencies detected
            MissingDependencyError: If required dependencies missing

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

        # Phase 1: Register all plugins and extract dependencies
        manifest_map: Dict[str, Path] = {}  # plugin_id -> manifest_path

        for manifest_path in manifest_paths:
            try:
                # Register plugin metadata (dependencies are parsed in register_from_manifest)
                metadata = self.register_from_manifest(manifest_path)
                logger.info(f"Registered plugin: {metadata.id} v{metadata.version}")
                manifest_map[metadata.id] = manifest_path

                logger.debug(f"Plugin {metadata.id} has dependencies: {list(metadata.dependencies.keys())}")

                # Phase 1 complete for this plugin - just registration

            except ManifestValidationError as e:
                logger.error(f"Manifest validation failed for {manifest_path}: {e}")
                failed.append((manifest_path, e))

            except Exception as e:
                logger.error(
                    f"Unexpected error loading plugin from {manifest_path}: {e}",
                    exc_info=True,
                )
                failed.append((manifest_path, e))

        # Phase 2: Build dependency graph and get load order
        try:
            self.build_dependency_graph()
            load_order = self.get_load_order()
            logger.info(f"Determined load order: {' -> '.join(load_order)}")
        except (CyclicDependencyError, MissingDependencyError) as e:
            logger.error(f"Dependency graph error: {e}")
            # All plugins failed due to dependency issues
            for plugin_id, manifest_path in manifest_map.items():
                failed.append((manifest_path, e))
                self.remove(plugin_id)
            return [], failed

        # Phase 3: Instantiate plugins in dependency order
        for plugin_id in load_order:
            manifest_path = manifest_map.get(plugin_id)
            if not manifest_path:
                continue  # Skip if already failed in registration

            metadata = self.get(plugin_id)
            if not metadata:
                continue

            try:
                # Load manifest to get entrypoint
                import yaml

                with open(manifest_path) as f:
                    manifest_data = yaml.safe_load(f)

                # Check if entrypoint is specified
                entrypoint = manifest_data.get("entrypoint")
                if not entrypoint:
                    logger.warning(f"Plugin {metadata.id} has no entrypoint, skipping instantiation")
                    loaded.append(metadata)
                    continue

                # Parse entrypoint object: {"module": "...", "class": "..."}
                if not isinstance(entrypoint, dict):
                    raise ValueError(
                        f"Invalid entrypoint format '{entrypoint}', " "expected object with 'module' and 'class' fields"
                    )

                module_path = entrypoint.get("module")
                class_name = entrypoint.get("class")

                if not module_path or not class_name:
                    raise ValueError("Entrypoint must have both 'module' and 'class' fields")

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
                        raise AttributeError(f"Module '{module_path}' has no class '{class_name}'")

                    plugin_class = getattr(module, class_name)
                    logger.debug(f"Found class: {class_name}")

                    # Instantiate plugin
                    # TODO: Pass configuration and dependencies when available
                    plugin_instance = plugin_class()
                    logger.info(f"Instantiated plugin: {metadata.id}")

                    # Store instance and module references for future reload
                    with self._lock:
                        self._instances[metadata.id] = plugin_instance
                        self._modules[metadata.id] = module

                    loaded.append(metadata)

                except (ImportError, AttributeError, TypeError) as e:
                    logger.error(
                        f"Failed to instantiate plugin {metadata.id}: {e}",
                        exc_info=True,
                    )
                    failed.append((manifest_path, e))
                    # Remove from registered plugins since instantiation failed
                    self.remove(metadata.id)

            except Exception as e:
                logger.error(f"Error instantiating plugin {plugin_id}: {e}", exc_info=True)
                failed.append((manifest_path, e))
                self.remove(plugin_id)

        logger.info(f"Plugin loading complete: {len(loaded)} successful, {len(failed)} failed")
        return loaded, failed


# Singleton for simple usage
manager = PluginManager()
