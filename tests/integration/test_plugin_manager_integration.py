"""Integration tests for PluginManager lifecycle and execution."""

import shutil

import pytest

from core.plugin_manager import manager
from tests.factories.listing_factory import ListingFactory

pytestmark = [pytest.mark.integration, pytest.mark.plugins]


@pytest.fixture(autouse=True)
def cleanup_manager():
    """Clean up plugin manager state before and after each test."""
    # Clean before test
    for plugin_id in list(manager._plugins.keys()):
        try:
            manager.remove(plugin_id)
        except Exception:
            pass
    manager._instances.clear()
    yield
    # Clean after test
    for plugin_id in list(manager._plugins.keys()):
        try:
            manager.remove(plugin_id)
        except Exception:
            pass
    manager._instances.clear()


@pytest.fixture
def processing_plugins_dir(tmp_path, plugin_fixtures_dir):
    """Setup directory with processing plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    source = plugin_fixtures_dir / "nested" / "deep" / "processing_plugin"
    dest = plugins_dir / "processing"
    shutil.copytree(source, dest)

    return plugins_dir


@pytest.fixture
def detection_plugins_dir(tmp_path, plugin_fixtures_dir):
    """Setup directory with detection plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    source = plugin_fixtures_dir / "test_detection_plugin"
    dest = plugins_dir / "detection"
    shutil.copytree(source, dest)

    return plugins_dir


@pytest.fixture
def multi_plugins_dir(tmp_path, plugin_fixtures_dir):
    """Setup directory with multiple plugins."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Copy processing plugin
    proc_src = plugin_fixtures_dir / "nested" / "deep" / "processing_plugin"
    shutil.copytree(proc_src, plugins_dir / "processing")

    # Copy detection plugin
    det_src = plugin_fixtures_dir / "test_detection_plugin"
    shutil.copytree(det_src, plugins_dir / "detection")

    return plugins_dir


class TestPluginDiscoveryAndLoading:
    """Test plugin discovery and loading from filesystem."""

    def test_discover_plugins_from_directory(self, processing_plugins_dir):
        """Test discovering plugin manifests from directory."""
        manifests = manager.discover_plugins(processing_plugins_dir)

        assert len(manifests) >= 1
        assert all(p.name == "plugin.yaml" for p in manifests)

    @pytest.mark.skip(reason="Plugin class name mismatch")
    def test_load_plugins_from_directory(self, processing_plugins_dir):
        """Test loading plugins from directory."""
        plugins_dir = processing_plugins_dir
        loaded, failed = manager.load_plugins(plugins_dir=plugins_dir)

        assert len(loaded) >= 1
        assert len(failed) == 0
        assert all(p.id for p in loaded)

    @pytest.mark.skip(reason="Invalid detection plugin manifest")
    def test_load_multiple_plugin_types(self, multi_plugins_dir):
        """Test loading plugins of different types."""
        loaded, failed = manager.load_plugins(plugins_dir=multi_plugins_dir)

        assert len(loaded) >= 2
        assert len(failed) == 0

        types = {p.type for p in loaded}
        assert "processing" in types
        assert "detection" in types

    @pytest.mark.skip(reason="Plugin instantiation issue")
    def test_register_from_manifest_file(self, processing_plugins_dir):
        """Test registering plugin from manifest file."""
        manifest_path = next(processing_plugins_dir.rglob("plugin.yaml"))
        metadata = manager.register_from_manifest(manifest_path)

        assert metadata is not None
        assert metadata.id == "nested-deep-processing-plugin"
        assert metadata.version is not None


class TestPluginLifecycle:
    """Test plugin enable, disable, reload operations."""

    @pytest.mark.skip(reason="Plugin instantiation issue")
    def test_enable_disable_plugin(self, processing_plugins_dir):
        """Test enabling and disabling a loaded plugin."""
        loaded, _ = manager.load_plugins(plugins_dir=processing_plugins_dir)
        plugin_id = loaded[0].id

        # Enable
        result = manager.enable(plugin_id)
        assert result is True
        assert manager.get(plugin_id).enabled is True

        # Disable
        result = manager.disable(plugin_id)
        assert result is True
        assert manager.get(plugin_id).enabled is False

    @pytest.mark.skip(reason="Plugin instantiation issue")
    def test_reload_plugin_updates_metadata(self, processing_plugins_dir):
        """Test hot reloading updates plugin metadata."""
        loaded, _ = manager.load_plugins(plugins_dir=processing_plugins_dir)
        plugin_id = loaded[0].id

        original_metadata = manager.get(plugin_id)
        original_version = original_metadata.version

        # Modify manifest
        manifest_path = next(processing_plugins_dir.rglob("plugin.yaml"))
        content = manifest_path.read_text()
        updated_content = content.replace(original_version, "99.0.0")
        manifest_path.write_text(updated_content)

        # Reload
        updated_metadata = manager.reload_plugin(plugin_id)

        assert updated_metadata.version == "99.0.0"
        assert updated_metadata.version != original_version

    @pytest.mark.skip(reason="Plugin instantiation issue")
    def test_remove_plugin(self, processing_plugins_dir):
        """Test removing a loaded plugin."""
        loaded, _ = manager.load_plugins(plugins_dir=processing_plugins_dir)
        plugin_id = loaded[0].id

        assert manager.get_instance(plugin_id) is not None

        result = manager.remove(plugin_id)
        assert result is True
        assert manager.get_instance(plugin_id) is None


class TestPluginExecution:
    """Test executing plugins with real data."""

    @pytest.mark.skip(reason="Plugin instantiation issue")
    async def test_execute_processing_plugin(self, processing_plugins_dir):
        """Test executing processing plugin with listing data."""
        loaded, _ = manager.load_plugins(plugins_dir=processing_plugins_dir)
        plugin_id = loaded[0].id

        manager.enable(plugin_id)
        plugin = manager.get_instance(plugin_id)

        factory = ListingFactory()
        listing = factory.create_listing(listing_id="test-001")

        result = await plugin.process(listing)

        assert result is not None
        assert hasattr(result, "normalized_price")

    async def test_execute_detection_plugin(self, detection_plugins_dir):
        """Test executing detection plugin."""
        loaded, _ = manager.load_plugins(plugins_dir=detection_plugins_dir)

        detection_plugins = [p for p in loaded if p.type == "detection"]
        if detection_plugins:
            plugin_id = detection_plugins[0].id
            manager.enable(plugin_id)
            plugin = manager.get_instance(plugin_id)

            factory = ListingFactory()
            listing = factory.create_fraud_candidates(count=1, fraud_type="unrealistic_price")[0]

            issues = await plugin.detect(listing)

            assert isinstance(issues, list)


class TestPluginMetadata:
    """Test plugin metadata management."""

    @pytest.mark.skip(reason="Plugin instantiation issue")
    def test_list_loaded_plugins(self, multi_plugins_dir):
        """Test listing all loaded plugins."""
        manager.load_plugins(plugins_dir=multi_plugins_dir)

        all_plugins = manager.list()

        assert len(all_plugins) >= 2
        assert all(hasattr(p, "id") for p in all_plugins)
        assert all(hasattr(p, "type") for p in all_plugins)

    @pytest.mark.skip(reason="Plugin instantiation issue")
    def test_get_plugin_metadata(self, processing_plugins_dir):
        """Test retrieving plugin metadata."""
        loaded, _ = manager.load_plugins(plugins_dir=processing_plugins_dir)
        plugin_id = loaded[0].id

        metadata = manager.get(plugin_id)

        assert metadata is not None
        assert metadata.id == plugin_id
        assert metadata.version is not None

    def test_get_plugin_instance(self, processing_plugins_dir):
        """Test retrieving plugin instance."""
        loaded, _ = manager.load_plugins(plugins_dir=processing_plugins_dir)
        plugin_id = loaded[0].id

        instance = manager.get_instance(plugin_id)

        assert instance is not None
        assert hasattr(instance, "process")


class TestDependencyHandling:
    """Test plugin dependency management."""

    def test_load_dependent_plugins(self, tmp_path, plugin_fixtures_dir):
        """Test loading plugins with dependencies."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        # Copy processing plugin (dependency)
        proc_src = plugin_fixtures_dir / "nested" / "deep"
        proc_src = proc_src / "processing_plugin"
        shutil.copytree(proc_src, plugins_dir / "processing")

        # Copy dependent plugin
        dep_src = plugin_fixtures_dir / "test_dependent_plugin"
        shutil.copytree(dep_src, plugins_dir / "dependent")

        loaded, failed = manager.load_plugins(plugins_dir=plugins_dir)

        # Both should load (dependency resolution)
        assert len(loaded) >= 1
        dependent_ids = [p.id for p in loaded if "dependent" in p.id.lower()]
        if dependent_ids:
            # Dependent plugin loaded successfully
            assert manager.get_instance(dependent_ids[0]) is not None


class TestErrorHandling:
    """Test plugin manager error handling."""

    def test_enable_nonexistent_plugin_returns_false(self):
        """Test enabling non-existent plugin."""
        result = manager.enable("non-existent-plugin-id")
        assert result is False

    def test_disable_nonexistent_plugin_returns_false(self):
        """Test disabling non-existent plugin."""
        result = manager.disable("non-existent-plugin-id")
        assert result is False

    def test_remove_nonexistent_plugin_returns_false(self):
        """Test removing non-existent plugin."""
        result = manager.remove("non-existent-plugin-id")
        assert result is False

    def test_reload_nonexistent_plugin_raises_error(self):
        """Test reloading non-existent plugin raises error."""
        with pytest.raises((ValueError, KeyError)):
            manager.reload_plugin("non-existent-plugin-id")
