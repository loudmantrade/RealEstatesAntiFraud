"""
Integration tests for PluginManager with manifest validation.
"""

from pathlib import Path

import pytest

from core.plugin_manager import PluginManager
from core.validators.manifest import ManifestValidationError

pytestmark = [pytest.mark.unit, pytest.mark.plugins]


@pytest.fixture
def plugin_manager():
    """Fresh PluginManager instance for each test."""
    return PluginManager()


@pytest.fixture
def valid_manifest_path():
    """Path to valid test manifest."""
    return Path(__file__).parent.parent / "fixtures" / "plugins" / "valid_source_plugin.yaml"


@pytest.fixture
def invalid_manifest_paths():
    """Paths to invalid test manifests."""
    base = Path(__file__).parent.parent / "fixtures" / "plugins"
    return {
        "missing_fields": base / "invalid_missing_fields.yaml",
        "bad_id": base / "invalid_id_pattern.yaml",
        "bad_version": base / "invalid_version.yaml",
    }


class TestPluginManagerValidation:
    """Test PluginManager integration with manifest validation."""

    def test_register_from_valid_manifest(self, plugin_manager, valid_manifest_path):
        """Should successfully register plugin from valid manifest."""
        plugin = plugin_manager.register_from_manifest(valid_manifest_path)

        assert plugin is not None
        assert plugin.id == "plugin-source-test-scraper"
        assert plugin.name == "Test Scraper Plugin"
        assert plugin.version == "1.0.0"
        assert plugin.type == "source"
        assert plugin.enabled is True

    def test_register_from_invalid_manifest_raises_error(self, plugin_manager, invalid_manifest_paths):
        """Should raise ManifestValidationError for invalid manifest."""
        with pytest.raises(ManifestValidationError) as exc_info:
            plugin_manager.register_from_manifest(invalid_manifest_paths["missing_fields"])

        error = exc_info.value
        assert len(error.errors) > 0

    def test_invalid_manifest_not_registered(self, plugin_manager, invalid_manifest_paths):
        """Invalid manifest should not be registered."""
        initial_count = len(plugin_manager.list())

        with pytest.raises(ManifestValidationError):
            plugin_manager.register_from_manifest(invalid_manifest_paths["bad_id"])

        # Plugin should not be in manager
        final_count = len(plugin_manager.list())
        assert final_count == initial_count

    def test_validation_error_contains_details(self, plugin_manager, invalid_manifest_paths):
        """Validation error should contain useful details."""
        with pytest.raises(ManifestValidationError) as exc_info:
            plugin_manager.register_from_manifest(invalid_manifest_paths["bad_version"])

        error = exc_info.value
        assert "invalid" in str(error).lower() or "validation" in str(error).lower()
        assert len(error.errors) > 0
        # Error should mention the problematic field
        assert any("version" in err.lower() for err in error.errors)

    def test_nonexistent_manifest_raises_error(self, plugin_manager):
        """Nonexistent manifest should raise error."""
        with pytest.raises(ManifestValidationError) as exc_info:
            plugin_manager.register_from_manifest(Path("/nonexistent/plugin.yaml"))

        error = exc_info.value
        assert "not found" in " ".join(error.errors).lower()

    def test_registered_plugin_can_be_retrieved(self, plugin_manager, valid_manifest_path):
        """Registered plugin should be retrievable by ID."""
        plugin = plugin_manager.register_from_manifest(valid_manifest_path)

        retrieved = plugin_manager.get(plugin.id)
        assert retrieved is not None
        assert retrieved.id == plugin.id
        assert retrieved.name == plugin.name

    def test_registered_plugin_appears_in_list(self, plugin_manager, valid_manifest_path):
        """Registered plugin should appear in list."""
        initial_count = len(plugin_manager.list())

        plugin = plugin_manager.register_from_manifest(valid_manifest_path)

        plugins = plugin_manager.list()
        assert len(plugins) == initial_count + 1
        assert any(p.id == plugin.id for p in plugins)

    def test_multiple_valid_manifests(self, plugin_manager, valid_manifest_path, tmp_path):
        """Should register multiple valid manifests."""
        # Register first plugin
        plugin1 = plugin_manager.register_from_manifest(valid_manifest_path)

        # Create second valid manifest
        import yaml

        manifest2_path = tmp_path / "plugin2.yaml"
        manifest2_data = {
            "id": "plugin-source-another",
            "name": "Another Plugin",
            "version": "2.0.0",
            "type": "source",
            "api_version": "1.0",
            "description": "Another test plugin",
        }
        with open(manifest2_path, "w") as f:
            yaml.dump(manifest2_data, f)

        # Register second plugin
        plugin2 = plugin_manager.register_from_manifest(manifest2_path)

        # Both should be registered
        plugins = plugin_manager.list()
        assert len(plugins) >= 2
        assert plugin1.id in [p.id for p in plugins]
        assert plugin2.id in [p.id for p in plugins]

    def test_validation_runs_before_registration(self, plugin_manager, invalid_manifest_paths):
        """Validation should happen before any registration attempt."""
        # Try to register invalid manifest
        try:
            plugin_manager.register_from_manifest(invalid_manifest_paths["bad_id"])
        except ManifestValidationError:
            pass

        # Manager should not have any plugins with invalid ID
        plugins = plugin_manager.list()
        assert not any(p.id == "bad_id_format" for p in plugins)


class TestPluginManagerErrorHandling:
    """Test error handling in PluginManager."""

    def test_yaml_syntax_error_handling(self, plugin_manager, tmp_path):
        """Should handle YAML syntax errors gracefully."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("invalid: yaml: [unclosed")

        with pytest.raises(ManifestValidationError) as exc_info:
            plugin_manager.register_from_manifest(bad_yaml)

        error = exc_info.value
        assert any("yaml" in err.lower() for err in error.errors)

    def test_empty_manifest_handling(self, plugin_manager, tmp_path):
        """Should handle empty manifest file."""
        empty_manifest = tmp_path / "empty.yaml"
        empty_manifest.write_text("")

        with pytest.raises(ManifestValidationError):
            plugin_manager.register_from_manifest(empty_manifest)

    def test_corrupted_manifest_handling(self, plugin_manager, tmp_path):
        """Should handle corrupted manifest data."""
        corrupt_manifest = tmp_path / "corrupt.yaml"
        corrupt_manifest.write_bytes(b"\x00\x01\x02\x03")

        with pytest.raises(ManifestValidationError):
            plugin_manager.register_from_manifest(corrupt_manifest)


class TestBackwardCompatibility:
    """Test backward compatibility with existing register() method."""

    def test_old_register_method_still_works(self, plugin_manager):
        """Old register() method should continue to work."""
        from core.models.plugin import PluginMetadata

        metadata = PluginMetadata(
            id="plugin-source-old",
            name="Old Style Plugin",
            version="1.0.0",
            type="source",
            enabled=True,
            config={},
        )

        plugin = plugin_manager.register(metadata)
        assert plugin.id == "plugin-source-old"

        retrieved = plugin_manager.get("plugin-source-old")
        assert retrieved is not None
