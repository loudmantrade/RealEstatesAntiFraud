"""
Integration tests for PluginManager with dependency graph

Tests plugin loading with dependencies in correct order,
cycle detection, and missing dependency handling.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

from core.plugin_manager import PluginManager
from core.dependency_graph import CyclicDependencyError, MissingDependencyError
from core.interfaces.source_plugin import SourcePlugin


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
    with open(manifest_path, 'w') as f:
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

    def validate(self, listing):
        return True
"""
        with open(module_file, 'w') as f:
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
                "entrypoint": {
                    "module": "plugin_a",
                    "class": "PluginA"
                }
            }
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
                "entrypoint": {
                    "module": "plugin_b",
                    "class": "PluginB"
                }
            }
        )

        # Load plugins
        manager = PluginManager()
        loaded, failed = manager.load_plugins(plugins_dir=temp_plugins_dir)

        assert len(loaded) == 2
        assert len(failed) == 0
        assert manager.get("plugin-source-a") is not None
        assert manager.get("plugin-source-b") is not None
