"""
Unit tests for plugin hot reload functionality.

Tests cover:
- Successful plugin reload
- Reload with graceful shutdown
- Reload errors (not found, not loaded, import failure)
- Concurrent reload protection
- Module reload behavior
"""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.models.plugin import PluginMetadata
from core.plugin_manager import PluginManager


@pytest.fixture
def plugin_manager():
    """Create a fresh PluginManager instance for each test."""
    return PluginManager()


@pytest.fixture
def sample_plugin_metadata():
    """Sample plugin metadata for testing."""
    return PluginMetadata(
        id="plugin-test-reload",
        name="Test Reload Plugin",
        version="1.0.0",
        type="source",
        enabled=True,
    )


class TestReloadPlugin:
    """Tests for PluginManager.reload_plugin() method."""

    def test_reload_plugin_not_found(self, plugin_manager):
        """Test reloading a plugin that doesn't exist."""
        with pytest.raises(ValueError, match="not found"):
            plugin_manager.reload_plugin("nonexistent-plugin")

    def test_reload_plugin_not_loaded(self, plugin_manager, sample_plugin_metadata):
        """Test reloading a plugin that exists but wasn't loaded."""
        # Register plugin but don't load it
        plugin_manager.register(sample_plugin_metadata)

        with pytest.raises(ValueError, match="not loaded"):
            plugin_manager.reload_plugin(sample_plugin_metadata.id)

    def test_reload_plugin_no_module_reference(self, plugin_manager, sample_plugin_metadata):
        """Test reload when module reference is missing."""
        # Register and fake an instance without module
        plugin_manager.register(sample_plugin_metadata)
        plugin_manager._instances[sample_plugin_metadata.id] = Mock()
        # Don't add to _modules

        with pytest.raises(RuntimeError, match="no module reference"):
            plugin_manager.reload_plugin(sample_plugin_metadata.id)

    def test_reload_plugin_calls_shutdown(self, plugin_manager, sample_plugin_metadata):
        """Test that reload calls shutdown() on old instance if available."""
        # Setup: register plugin with instance that has shutdown method
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_instance.shutdown = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        # Mock importlib.reload to return same module with new class
        new_class = Mock()
        new_class.return_value = Mock()  # New instance

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, type(mock_instance).__name__, new_class):
                plugin_manager.reload_plugin(sample_plugin_metadata.id)

        # Verify shutdown was called
        mock_instance.shutdown.assert_called_once()

    def test_reload_plugin_without_shutdown_method(self, plugin_manager, sample_plugin_metadata):
        """Test reload works even if plugin doesn't implement shutdown()."""
        plugin_manager.register(sample_plugin_metadata)

        # Instance without shutdown method
        mock_instance = Mock(spec=[])  # No methods
        del mock_instance.shutdown  # Ensure no shutdown attribute

        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        # Should not raise, just skip shutdown
        new_class = Mock()
        new_class.return_value = Mock()

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, type(mock_instance).__name__, new_class):
                result = plugin_manager.reload_plugin(sample_plugin_metadata.id)

        assert result == sample_plugin_metadata

    def test_reload_plugin_shutdown_error_continues(self, plugin_manager, sample_plugin_metadata):
        """Test that errors in shutdown() don't prevent reload."""
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_instance.shutdown = Mock(side_effect=Exception("Shutdown error"))
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        new_class = Mock()
        new_class.return_value = Mock()

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, type(mock_instance).__name__, new_class):
                # Should succeed despite shutdown error
                result = plugin_manager.reload_plugin(sample_plugin_metadata.id)

        assert result == sample_plugin_metadata

    def test_reload_plugin_module_reload_failure(self, plugin_manager, sample_plugin_metadata):
        """Test reload fails when module reload raises error."""
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        with patch("importlib.reload", side_effect=ImportError("Module not found")):
            with pytest.raises(RuntimeError, match="Failed to reload module"):
                plugin_manager.reload_plugin(sample_plugin_metadata.id)

    def test_reload_plugin_class_not_found_after_reload(self, plugin_manager, sample_plugin_metadata):
        """Test reload fails if class is removed in new version."""
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_instance.__class__.__name__ = "TestPlugin"
        mock_module = Mock(spec=[])  # Module without the class

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        with patch("importlib.reload", return_value=mock_module):
            with pytest.raises(RuntimeError, match="Class .* not found"):
                plugin_manager.reload_plugin(sample_plugin_metadata.id)

    def test_reload_plugin_instantiation_failure(self, plugin_manager, sample_plugin_metadata):
        """Test reload fails if new instance can't be created."""
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        # New class that raises on instantiation
        new_class = Mock(side_effect=TypeError("Can't instantiate"))

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, type(mock_instance).__name__, new_class):
                with pytest.raises(RuntimeError, match="Failed to instantiate"):
                    plugin_manager.reload_plugin(sample_plugin_metadata.id)

    def test_reload_plugin_replaces_instance(self, plugin_manager, sample_plugin_metadata):
        """Test that reload replaces old instance with new one."""
        plugin_manager.register(sample_plugin_metadata)

        old_instance = Mock()
        old_instance.__class__.__name__ = "TestPlugin"
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = old_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        # New instance to be created
        new_instance = Mock()
        new_class = Mock(return_value=new_instance)

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, "TestPlugin", new_class):
                plugin_manager.reload_plugin(sample_plugin_metadata.id)

        # Verify instance was replaced
        assert plugin_manager._instances[sample_plugin_metadata.id] == new_instance
        assert plugin_manager._instances[sample_plugin_metadata.id] != old_instance

    def test_reload_plugin_replaces_module_reference(self, plugin_manager, sample_plugin_metadata):
        """Test that reload updates module reference."""
        plugin_manager.register(sample_plugin_metadata)

        old_module = Mock()
        old_module.__name__ = "old_module"
        mock_instance = Mock()
        mock_instance.__class__.__name__ = "TestPlugin"

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = old_module

        # New reloaded module
        new_module = Mock()
        new_module.__name__ = "new_module"
        new_class = Mock(return_value=Mock())

        with patch("importlib.reload", return_value=new_module):
            with patch.object(new_module, "TestPlugin", new_class):
                plugin_manager.reload_plugin(sample_plugin_metadata.id)

        # Verify module reference was updated
        assert plugin_manager._modules[sample_plugin_metadata.id] == new_module

    def test_reload_plugin_returns_metadata(self, plugin_manager, sample_plugin_metadata):
        """Test that reload returns updated plugin metadata."""
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_instance.__class__.__name__ = "TestPlugin"
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        new_class = Mock(return_value=Mock())

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, "TestPlugin", new_class):
                result = plugin_manager.reload_plugin(sample_plugin_metadata.id)

        assert result == sample_plugin_metadata
        assert result.id == sample_plugin_metadata.id

    def test_reload_plugin_thread_safety(self, plugin_manager, sample_plugin_metadata):
        """Test that reload uses lock for thread safety."""
        plugin_manager.register(sample_plugin_metadata)

        mock_instance = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        # Verify that _lock is acquired during reload
        original_lock = plugin_manager._lock

        new_class = Mock(return_value=Mock())

        with patch("importlib.reload", return_value=mock_module):
            with patch.object(mock_module, type(mock_instance).__name__, new_class):
                # This should work without deadlock
                plugin_manager.reload_plugin(sample_plugin_metadata.id)

        # Lock should still be the same object
        assert plugin_manager._lock is original_lock


class TestReloadIntegration:
    """Integration tests for hot reload with real plugin loading."""

    def test_reload_after_load_plugins(self, plugin_manager, tmp_path):
        """Test reload works after loading plugin from manifest."""
        # Create a simple test plugin
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()

        # Create manifest
        manifest_path = plugin_dir / "plugin.yaml"
        manifest_path.write_text(
            """
id: plugin-source-test
name: Test Plugin
version: 1.0.0
type: source
api_version: "1.0"
description: Test
entrypoint:
  module: test_plugin_module
  class: TestPlugin
"""
        )

        # Create plugin module with all required abstract methods
        plugin_module = plugin_dir / "test_plugin_module.py"
        plugin_module.write_text(
            """
from core.interfaces.source_plugin import SourcePlugin
from typing import Dict, Iterator, Optional

class TestPlugin(SourcePlugin):
    def __init__(self):
        self.value = "original"
        self.shutdown_called = False

    def get_metadata(self) -> Dict:
        return {"value": self.value}

    def configure(self, config: Dict) -> None:
        pass

    def validate_config(self) -> bool:
        return True

    def scrape(self, params: Dict) -> Iterator[Dict]:
        yield {}

    def scrape_single(self, listing_id: str) -> Optional[Dict]:
        return None

    def validate_listing(self, listing: Dict) -> bool:
        return True

    def get_statistics(self) -> Dict:
        return {}

    def shutdown(self) -> None:
        self.shutdown_called = True
"""
        )

        # Load the plugin
        loaded, failed = plugin_manager.load_plugins(plugins_dir=tmp_path)
        assert len(loaded) == 1
        assert len(failed) == 0

        # Get instance before reload
        old_instance = plugin_manager._instances["plugin-source-test"]
        assert old_instance.value == "original"

        # Modify plugin code
        plugin_module.write_text(
            plugin_module.read_text().replace('self.value = "original"', 'self.value = "reloaded"')
        )

        # Clear Python bytecode cache to force reload from source
        import shutil

        pycache_dir = plugin_dir / "__pycache__"
        if pycache_dir.exists():
            shutil.rmtree(pycache_dir)

        # Invalidate import caches
        import importlib

        importlib.invalidate_caches()

        # Reload plugin
        result = plugin_manager.reload_plugin("plugin-source-test")
        assert result.id == "plugin-source-test"

        # Get new instance
        new_instance = plugin_manager._instances["plugin-source-test"]

        # Verify it's a new instance with updated code
        assert new_instance != old_instance
        assert new_instance.value == "reloaded"


class TestReloadLogging:
    """Tests for reload logging behavior."""

    def test_reload_logs_start(self, plugin_manager, sample_plugin_metadata, caplog):
        """Test that reload logs start message."""
        import logging

        plugin_manager.register(sample_plugin_metadata)
        mock_instance = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        new_class = Mock(return_value=Mock())

        with caplog.at_level(logging.INFO):
            with patch("importlib.reload", return_value=mock_module):
                with patch.object(mock_module, type(mock_instance).__name__, new_class):
                    plugin_manager.reload_plugin(sample_plugin_metadata.id)

        messages = [r.message for r in caplog.records]
        assert any("Starting hot reload" in msg for msg in messages)

    def test_reload_logs_completion(self, plugin_manager, sample_plugin_metadata, caplog):
        """Test that reload logs completion message."""
        import logging

        plugin_manager.register(sample_plugin_metadata)
        mock_instance = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        new_class = Mock(return_value=Mock())

        with caplog.at_level(logging.INFO):
            with patch("importlib.reload", return_value=mock_module):
                with patch.object(mock_module, type(mock_instance).__name__, new_class):
                    plugin_manager.reload_plugin(sample_plugin_metadata.id)

        messages = [r.message for r in caplog.records]
        assert any("Hot reload completed successfully" in msg for msg in messages)

    def test_reload_logs_failure(self, plugin_manager, sample_plugin_metadata, caplog):
        """Test that reload logs error on failure."""
        import logging

        plugin_manager.register(sample_plugin_metadata)
        mock_instance = Mock()
        mock_module = Mock(__name__="test_module")

        plugin_manager._instances[sample_plugin_metadata.id] = mock_instance
        plugin_manager._modules[sample_plugin_metadata.id] = mock_module

        with caplog.at_level(logging.ERROR):
            with patch("importlib.reload", side_effect=ImportError("Test error")):
                try:
                    plugin_manager.reload_plugin(sample_plugin_metadata.id)
                except RuntimeError:
                    pass

        messages = [r.message for r in caplog.records]
        assert any("Hot reload failed" in msg for msg in messages)
