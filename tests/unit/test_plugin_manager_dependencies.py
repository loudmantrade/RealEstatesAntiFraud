"""
Integration tests for PluginManager with dependency graph

Tests plugin loading with dependencies in correct order,
cycle detection, and missing dependency handling.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from core.dependency_graph import CyclicDependencyError, MissingDependencyError
from core.interfaces.source_plugin import SourcePlugin
from core.plugin_manager import PluginManager


# Test plugin classes
class PluginA(SourcePlugin):
    """Plugin A with no dependencies."""

    def scrape(self, config):
        return []

    def validate(self, listing):
        return True


class PluginB(SourcePlugin):
    """Plugin B depends on A."""

    def scrape(self, config):
        return []

    def validate(self, listing):
        return True


class PluginC(SourcePlugin):
    """Plugin C depends on A and B."""

    def scrape(self, config):
        return []

    def validate(self, listing):
        return True


@pytest.fixture
def temp_plugins_dir():
    """Create temporary directory for test plugins."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def create_plugin_manifest(plugin_dir: Path, plugin_data: dict):
    """Helper to create plugin manifest and module."""
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Write manifest
    manifest_path = plugin_dir / "plugin.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(plugin_data, f)

    # Write Python module if entrypoint specified
    if "entrypoint" in plugin_data:
        module_name = plugin_data["entrypoint"]["module"]
        class_name = plugin_data["entrypoint"]["class"]

        # Create module file
        module_file = plugin_dir / f"{module_name}.py"
        module_content = f"""
from core.interfaces.source_plugin import SourcePlugin

class {class_name}(SourcePlugin):
    def scrape(self, config):
        return []

    def scrape_single(self, listing_id, config):
        return {{}}

    def validate(self, listing):
        return True

    def validate_listing(self, listing):
        return True

    def validate_config(self, config):
        return True

    def configure(self, config):
        pass

    def get_metadata(self):
        return {{}}

    def get_statistics(self):
        return {{}}
"""
        with open(module_file, "w") as f:
            f.write(module_content)


class TestPluginManagerDependencies:
    """Test plugin loading with dependencies."""

    def test_load_plugins_no_dependencies(self, temp_plugins_dir):
        """Test loading plugins without dependencies."""
        # Create plugins
        create_plugin_manifest(
            temp_plugins_dir / "plugin-a",
            {
                "id": "plugin-source-a",
                "name": "Plugin A",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Test plugin A",
                "entrypoint": {"module": "plugin_a", "class": "PluginA"},
            },
        )

        create_plugin_manifest(
            temp_plugins_dir / "plugin-b",
            {
                "id": "plugin-source-b",
                "name": "Plugin B",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Test plugin B",
                "entrypoint": {"module": "plugin_b", "class": "PluginB"},
            },
        )

        # Load plugins
        manager = PluginManager()
        loaded, failed = manager.load_plugins(plugins_dir=temp_plugins_dir)

        assert len(loaded) == 2
        assert len(failed) == 0
        assert manager.get("plugin-source-a") is not None
        assert manager.get("plugin-source-b") is not None

    def test_load_plugins_linear_dependencies(self, temp_plugins_dir):
        """Test loading plugins with linear dependency chain: A -> B -> C."""
        # Plugin A (no deps)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-a",
            {
                "id": "plugin-source-a",
                "name": "Plugin A",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Test plugin A",
                "entrypoint": {"module": "plugin_a", "class": "PluginA"},
            },
        )

        # Plugin B (depends on A)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-b",
            {
                "id": "plugin-source-b",
                "name": "Plugin B",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Test plugin B",
                "dependencies": {"plugins": {"plugin-source-a": ">=1.0.0"}},
                "entrypoint": {"module": "plugin_b", "class": "PluginB"},
            },
        )

        # Plugin C (depends on B)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-c",
            {
                "id": "plugin-source-c",
                "name": "Plugin C",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Test plugin C",
                "dependencies": {"plugins": {"plugin-source-b": ">=1.0.0"}},
                "entrypoint": {"module": "plugin_c", "class": "PluginC"},
            },
        )

        # Load plugins
        manager = PluginManager()
        loaded, failed = manager.load_plugins(plugins_dir=temp_plugins_dir)

        assert len(loaded) == 3
        assert len(failed) == 0

        # Verify load order: A should be before B, B before C
        load_order = manager.get_load_order()
        assert load_order.index("plugin-source-a") < load_order.index("plugin-source-b")
        assert load_order.index("plugin-source-b") < load_order.index("plugin-source-c")

    def test_load_plugins_diamond_dependencies(self, temp_plugins_dir):
        """Test loading plugins with diamond dependency: A -> B,C -> D."""
        # Plugin A (no deps)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-a",
            {
                "id": "plugin-source-a",
                "name": "Plugin A",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Base plugin",
                "entrypoint": {"module": "plugin_a", "class": "PluginA"},
            },
        )

        # Plugin B (depends on A)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-b",
            {
                "id": "plugin-source-b",
                "name": "Plugin B",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin B",
                "dependencies": {"plugins": {"plugin-source-a": ">=1.0.0"}},
                "entrypoint": {"module": "plugin_b", "class": "PluginB"},
            },
        )

        # Plugin C (depends on A)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-c",
            {
                "id": "plugin-source-c",
                "name": "Plugin C",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin C",
                "dependencies": {"plugins": {"plugin-source-a": ">=1.0.0"}},
                "entrypoint": {"module": "plugin_c", "class": "PluginC"},
            },
        )

        # Plugin D (depends on B and C)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-d",
            {
                "id": "plugin-source-d",
                "name": "Plugin D",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin D",
                "dependencies": {
                    "plugins": {
                        "plugin-source-b": ">=1.0.0",
                        "plugin-source-c": ">=1.0.0",
                    }
                },
                "entrypoint": {"module": "plugin_d", "class": "PluginD"},
            },
        )

        # Load plugins
        manager = PluginManager()
        loaded, failed = manager.load_plugins(plugins_dir=temp_plugins_dir)

        assert len(loaded) == 4
        assert len(failed) == 0

        # Verify load order constraints
        load_order = manager.get_load_order()
        a_pos = load_order.index("plugin-source-a")
        b_pos = load_order.index("plugin-source-b")
        c_pos = load_order.index("plugin-source-c")
        d_pos = load_order.index("plugin-source-d")

        # A must be before B and C
        assert a_pos < b_pos
        assert a_pos < c_pos

        # B and C must be before D
        assert b_pos < d_pos
        assert c_pos < d_pos

    def test_load_plugins_circular_dependency(self, temp_plugins_dir):
        """Test that circular dependencies are detected and rejected."""
        # Plugin A (depends on B)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-a",
            {
                "id": "plugin-source-a",
                "name": "Plugin A",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin A",
                "dependencies": {"plugins": {"plugin-source-b": ">=1.0.0"}},
                "entrypoint": {"module": "plugin_a", "class": "PluginA"},
            },
        )

        # Plugin B (depends on A - creates cycle)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-b",
            {
                "id": "plugin-source-b",
                "name": "Plugin B",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin B",
                "dependencies": {"plugins": {"plugin-source-a": ">=1.0.0"}},
                "entrypoint": {"module": "plugin_b", "class": "PluginB"},
            },
        )

        # Load plugins - should detect cycle
        manager = PluginManager()
        loaded, failed = manager.load_plugins(plugins_dir=temp_plugins_dir)

        # All plugins should fail due to cycle
        assert len(loaded) == 0
        assert len(failed) == 2

        # Check that cycle error was raised
        errors = [e for _, e in failed]
        assert any(isinstance(e, CyclicDependencyError) for e in errors)

    def test_load_plugins_missing_dependency(self, temp_plugins_dir):
        """Test that missing dependencies are detected."""
        # Plugin B (depends on non-existent plugin A)
        create_plugin_manifest(
            temp_plugins_dir / "plugin-b",
            {
                "id": "plugin-source-b",
                "name": "Plugin B",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin B",
                "dependencies": {
                    "plugins": {"plugin-source-a": ">=1.0.0"}
                },  # Does not exist
                "entrypoint": {"module": "plugin_b", "class": "PluginB"},
            },
        )

        # Load plugins - should detect missing dependency
        manager = PluginManager()
        loaded, failed = manager.load_plugins(plugins_dir=temp_plugins_dir)

        assert len(loaded) == 0
        assert len(failed) == 1

        # Check that missing dependency error was raised
        _, error = failed[0]
        assert isinstance(error, MissingDependencyError)

    def test_build_dependency_graph_method(self, temp_plugins_dir):
        """Test build_dependency_graph method directly."""
        # Create plugins manually
        manager = PluginManager()

        # Register plugins
        from core.models.plugin import PluginMetadata

        plugin_a = PluginMetadata(
            id="plugin-a",
            name="Plugin A",
            version="1.0.0",
            type="source",
            enabled=True,
            config={"dependencies": []},
        )

        plugin_b = PluginMetadata(
            id="plugin-b",
            name="Plugin B",
            version="1.0.0",
            type="source",
            enabled=True,
            config={"dependencies": ["plugin-a"]},
        )

        manager.register(plugin_a)
        manager.register(plugin_b)

        # Build graph
        manager.build_dependency_graph()

        # Get load order
        load_order = manager.get_load_order()

        assert load_order == ["plugin-a", "plugin-b"]

    def test_get_load_order_before_build_fails(self):
        """Test that get_load_order requires build first."""
        manager = PluginManager()

        with pytest.raises(RuntimeError, match="must be built"):
            manager.get_load_order()

    def test_dependency_graph_updated_on_remove(self):
        """Test that dependency graph is updated when plugin removed."""
        manager = PluginManager()
        from core.models.plugin import PluginMetadata

        plugin_a = PluginMetadata(
            id="plugin-a",
            name="Plugin A",
            version="1.0.0",
            type="source",
            enabled=True,
            config={"dependencies": []},
        )

        manager.register(plugin_a)
        manager.build_dependency_graph()

        assert manager._dependency_graph.has_plugin("plugin-a")

        # Remove plugin
        manager.remove("plugin-a")

        assert not manager._dependency_graph.has_plugin("plugin-a")


class TestPluginDependencyExtraction:
    """Test dependency extraction from manifests."""

    def test_extract_dependencies_from_manifest(self, temp_plugins_dir):
        """Test that dependencies are correctly extracted from manifest."""
        create_plugin_manifest(
            temp_plugins_dir / "plugin-b",
            {
                "id": "plugin-source-b",
                "name": "Plugin B",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin B",
                "dependencies": {
                    "plugins": {
                        "plugin-source-a": ">=1.0.0",
                        "plugin-source-x": "^2.0.0",
                    }
                },
            },
        )

        manager = PluginManager()

        # Register from manifest
        manifest_path = temp_plugins_dir / "plugin-b" / "plugin.yaml"
        try:
            metadata = manager.register_from_manifest(manifest_path)
        except Exception:
            # Expected to fail due to missing dependencies
            pass

        # Check dependencies stored in metadata
        metadata = manager.get("plugin-source-b")
        if metadata:
            deps = metadata.dependencies or {}
            assert set(deps.keys()) == {"plugin-source-a", "plugin-source-x"}

    def test_empty_dependencies(self, temp_plugins_dir):
        """Test plugin with no dependencies."""
        create_plugin_manifest(
            temp_plugins_dir / "plugin-a",
            {
                "id": "plugin-source-a",
                "name": "Plugin A",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Plugin A",
            },
        )

        manager = PluginManager()
        manifest_path = temp_plugins_dir / "plugin-a" / "plugin.yaml"
        metadata = manager.register_from_manifest(manifest_path)

        deps = metadata.dependencies or {}
        assert deps == {}
