"""Unit tests for plugin discovery and loading."""

import logging
import shutil
import tempfile
from pathlib import Path

import pytest

from core.plugin_manager import PluginManager
from core.validators.manifest import ManifestValidationError

pytestmark = [pytest.mark.unit, pytest.mark.plugins]


@pytest.fixture
def plugins_dir():
    """Fixture providing path to test plugins directory."""
    return Path(__file__).parent.parent / "fixtures" / "plugins"


@pytest.fixture
def plugin_manager():
    """Fixture providing fresh PluginManager instance."""
    return PluginManager()


@pytest.fixture
def temp_plugins_dir():
    """Fixture providing temporary directory for hot-drop tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestDiscoverPlugins:
    """Test plugin discovery functionality."""

    def test_discover_valid_plugins(self, plugin_manager, plugins_dir):
        """Test discovery finds valid plugin manifests."""
        manifests = plugin_manager.discover_plugins(plugins_dir)

        # Should find at least our test plugins
        assert len(manifests) > 0

        # All discovered paths should exist and be plugin.yaml files
        for manifest in manifests:
            assert manifest.exists()
            assert manifest.name == "plugin.yaml"

    def test_discover_nested_plugins(self, plugin_manager, plugins_dir):
        """Test discovery finds plugins in nested directories."""
        manifests = plugin_manager.discover_plugins(plugins_dir)

        # Should find nested plugin
        nested_found = any("nested" in str(m) for m in manifests)
        assert nested_found, "Should discover plugins in nested directories"

    def test_discover_nonexistent_directory(self, plugin_manager):
        """Test discovery handles non-existent directory gracefully."""
        nonexistent = Path("/nonexistent/path/to/plugins")
        manifests = plugin_manager.discover_plugins(nonexistent)

        assert manifests == []

    def test_discover_file_instead_of_directory(self, plugin_manager, tmp_path):
        """Test discovery handles file path instead of directory."""
        test_file = tmp_path / "not_a_directory.txt"
        test_file.write_text("test")

        manifests = plugin_manager.discover_plugins(test_file)

        assert manifests == []

    def test_discover_empty_directory(self, plugin_manager, tmp_path):
        """Test discovery in empty directory returns no manifests."""
        manifests = plugin_manager.discover_plugins(tmp_path)

        assert manifests == []

    def test_discover_validates_manifests(self, plugin_manager, plugins_dir, caplog):
        """Test discovery validates and skips invalid manifests."""
        with caplog.at_level(logging.ERROR):
            manifests = plugin_manager.discover_plugins(plugins_dir)

        # Should log errors for invalid manifests
        # Check that invalid manifests in fixtures/ are detected
        invalid_logged = any("Invalid manifest" in record.message for record in caplog.records)

        # If we have invalid YAML files in fixtures, they should be logged
        # (we have invalid_*.yaml files in fixtures/plugins/)

    def test_discover_returns_only_valid(self, plugin_manager, plugins_dir):
        """Test discovery only returns valid manifests."""
        manifests = plugin_manager.discover_plugins(plugins_dir)

        # All returned manifests should be valid
        from core.validators.manifest import validate_manifest

        for manifest in manifests:
            is_valid, errors = validate_manifest(manifest)
            assert is_valid, f"Discovered manifest {manifest} should be valid: {errors}"


class TestLoadPlugins:
    """Test plugin loading functionality."""

    def test_load_plugin_with_entrypoint(self, plugin_manager, plugins_dir):
        """Test loading plugin that has valid entrypoint."""
        # Load only the test source plugin
        test_plugin_manifest = plugins_dir / "test_source_plugin" / "plugin.yaml"

        loaded, failed = plugin_manager.load_plugins(manifest_paths=[test_plugin_manifest])

        assert len(loaded) == 1
        assert len(failed) == 0

        plugin = loaded[0]
        assert plugin.id == "plugin-source-test-cian"
        assert plugin.name == "Test Cian Source Plugin"
        assert plugin.version == "1.0.0"
        assert plugin.type == "source"

    def test_load_plugin_without_entrypoint(self, plugin_manager, plugins_dir, caplog):
        """Test loading plugin without entrypoint skips instantiation."""
        manifest = plugins_dir / "no_entrypoint_plugin" / "plugin.yaml"

        with caplog.at_level(logging.WARNING):
            loaded, failed = plugin_manager.load_plugins(manifest_paths=[manifest])

        # Should register but not instantiate
        assert len(loaded) == 1
        assert len(failed) == 0

        # Should log warning about missing entrypoint
        assert any("no entrypoint" in record.message.lower() for record in caplog.records)

    def test_load_plugin_with_import_error(self, plugin_manager, plugins_dir):
        """Test loading plugin with non-existent module."""
        manifest = plugins_dir / "bad_entrypoint_plugin" / "plugin.yaml"

        loaded, failed = plugin_manager.load_plugins(manifest_paths=[manifest])

        # Should fail to load
        assert len(loaded) == 0
        assert len(failed) == 1

        failed_path, exception = failed[0]
        assert failed_path == manifest
        assert isinstance(exception, (ImportError, AttributeError))

    def test_load_plugin_with_init_error(self, plugin_manager, plugins_dir):
        """Test loading plugin that fails during initialization."""
        manifest = plugins_dir / "init_error_plugin" / "plugin.yaml"

        loaded, failed = plugin_manager.load_plugins(manifest_paths=[manifest])

        # Should fail to load
        assert len(loaded) == 0
        assert len(failed) == 1

        failed_path, exception = failed[0]
        assert failed_path == manifest
        assert isinstance(exception, (TypeError, RuntimeError))

    def test_load_multiple_plugins(self, plugin_manager, plugins_dir):
        """Test loading multiple plugins at once."""
        manifests = [
            plugins_dir / "test_source_plugin" / "plugin.yaml",
            plugins_dir / "no_entrypoint_plugin" / "plugin.yaml",
        ]

        loaded, failed = plugin_manager.load_plugins(manifest_paths=manifests)

        # Both should load (one with entrypoint, one without)
        assert len(loaded) == 2
        assert len(failed) == 0

    def test_load_from_directory(self, plugin_manager, plugins_dir):
        """Test auto-discovery and loading from directory."""
        loaded, failed = plugin_manager.load_plugins(plugins_dir=plugins_dir)

        # Should find and attempt to load multiple plugins
        total = len(loaded) + len(failed)
        assert total > 0

        # At least test_source_plugin should load successfully
        assert any(p.id == "plugin-source-test-cian" for p in loaded)

    def test_load_requires_path_or_directory(self, plugin_manager):
        """Test load_plugins raises error without paths or directory."""
        with pytest.raises(ValueError, match="Either manifest_paths or plugins_dir"):
            plugin_manager.load_plugins()

    def test_load_registers_metadata(self, plugin_manager, plugins_dir):
        """Test loaded plugins are registered in manager."""
        manifest = plugins_dir / "test_source_plugin" / "plugin.yaml"

        loaded, _ = plugin_manager.load_plugins(manifest_paths=[manifest])

        # Should be retrievable from manager
        plugin = plugin_manager.get("plugin-source-test-cian")
        assert plugin is not None
        assert plugin.name == "Test Cian Source Plugin"

    def test_load_failure_removes_registration(self, plugin_manager, plugins_dir):
        """Test failed plugin instantiation removes registration."""
        manifest = plugins_dir / "init_error_plugin" / "plugin.yaml"

        plugin_manager.load_plugins(manifest_paths=[manifest])

        # Failed plugin should not be registered
        plugin = plugin_manager.get("plugin-source-init-error")
        assert plugin is None

    def test_load_partial_failure(self, plugin_manager, plugins_dir):
        """Test loading continues after individual plugin failures."""
        manifests = [
            plugins_dir / "test_source_plugin" / "plugin.yaml",
            plugins_dir / "bad_entrypoint_plugin" / "plugin.yaml",
            plugins_dir / "no_entrypoint_plugin" / "plugin.yaml",
        ]

        loaded, failed = plugin_manager.load_plugins(manifest_paths=manifests)

        # Should have both successes and failures
        assert len(loaded) > 0
        assert len(failed) > 0

        # Successful ones should be registered
        assert plugin_manager.get("plugin-source-test-cian") is not None


class TestHotDropIntegration:
    """Test hot-drop plugin loading (adding plugin after initialization)."""

    def test_discover_new_plugin_after_init(self, plugin_manager, temp_plugins_dir, plugins_dir):
        """Test discovering new plugin added after initialization."""
        # Initial discovery - should be empty
        manifests = plugin_manager.discover_plugins(temp_plugins_dir)
        assert len(manifests) == 0

        # Copy a plugin to temp directory
        source_plugin = plugins_dir / "test_source_plugin"
        dest_plugin = temp_plugins_dir / "test_source_plugin"
        shutil.copytree(source_plugin, dest_plugin)

        # Discover again - should find new plugin
        manifests = plugin_manager.discover_plugins(temp_plugins_dir)
        assert len(manifests) == 1
        assert manifests[0] == dest_plugin / "plugin.yaml"

    def test_load_new_plugin_hot_drop(self, plugin_manager, temp_plugins_dir, plugins_dir):
        """Test loading new plugin added after initialization."""
        # Load from empty directory
        loaded, _ = plugin_manager.load_plugins(plugins_dir=temp_plugins_dir)
        assert len(loaded) == 0
        assert len(plugin_manager.list()) == 0

        # Add a plugin
        source_plugin = plugins_dir / "test_source_plugin"
        dest_plugin = temp_plugins_dir / "test_source_plugin"
        shutil.copytree(source_plugin, dest_plugin)

        # Load again - should find and load new plugin
        loaded, failed = plugin_manager.load_plugins(plugins_dir=temp_plugins_dir)

        assert len(loaded) == 1
        assert len(failed) == 0
        assert plugin_manager.get("plugin-source-test-cian") is not None

    def test_multiple_hot_drops(self, plugin_manager, temp_plugins_dir, plugins_dir):
        """Test multiple sequential hot drops."""
        # First hot drop
        source1 = plugins_dir / "test_source_plugin"
        dest1 = temp_plugins_dir / "plugin1"
        shutil.copytree(source1, dest1)

        loaded, _ = plugin_manager.load_plugins(plugins_dir=temp_plugins_dir)
        assert len(loaded) == 1

        # Second hot drop
        source2 = plugins_dir / "no_entrypoint_plugin"
        dest2 = temp_plugins_dir / "plugin2"
        shutil.copytree(source2, dest2)

        # Create new manager instance to simulate fresh discovery
        new_manager = PluginManager()
        loaded, _ = new_manager.load_plugins(plugins_dir=temp_plugins_dir)

        # Should find both plugins
        assert len(loaded) == 2


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_entrypoint_format(self, plugin_manager, tmp_path):
        """Test handling of entrypoint without colon separator."""
        manifest_path = tmp_path / "plugin.yaml"
        manifest_path.write_text(
            """
id: plugin-source-test
name: Test Plugin
version: 1.0.0
type: source
api_version: "1.0"
description: Test
entrypoint: invalid_format_no_colon
"""
        )

        loaded, failed = plugin_manager.load_plugins(manifest_paths=[manifest_path])

        assert len(loaded) == 0
        assert len(failed) == 1
        assert isinstance(failed[0][1], (ValueError, ManifestValidationError))

    def test_logging_on_success(self, plugin_manager, plugins_dir, caplog):
        """Test appropriate logging on successful plugin loading."""
        manifest = plugins_dir / "test_source_plugin" / "plugin.yaml"

        with caplog.at_level(logging.INFO):
            plugin_manager.load_plugins(manifest_paths=[manifest])

        # Should log registration and instantiation
        messages = [r.message for r in caplog.records]
        assert any("Registered plugin" in msg for msg in messages)
        assert any("Instantiated plugin" in msg for msg in messages)

    def test_logging_on_failure(self, plugin_manager, plugins_dir, caplog):
        """Test appropriate logging on plugin loading failure."""
        manifest = plugins_dir / "bad_entrypoint_plugin" / "plugin.yaml"

        with caplog.at_level(logging.ERROR):
            plugin_manager.load_plugins(manifest_paths=[manifest])

        # Should log error details
        assert any("Failed to instantiate" in r.message for r in caplog.records)
