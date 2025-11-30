"""Tests for detection plugin registry integration."""

from unittest.mock import MagicMock

import pytest

from core.fraud.detection_plugin_wrapper import DetectionPluginWrapper
from core.interfaces.detection_plugin import DetectionPlugin
from core.models.plugin import PluginMetadata
from core.plugin_manager import PluginManager

pytestmark = [pytest.mark.unit, pytest.mark.plugins]


class MockDetectionPlugin(DetectionPlugin):
    """Mock detection plugin for testing."""

    def __init__(self, plugin_id: str, default_weight: float = 0.5):
        self.plugin_id = plugin_id
        self.default_weight = default_weight
        self.analyze_called = False
        self.shutdown_called = False

    def get_metadata(self):
        return {
            "id": self.plugin_id,
            "name": f"Mock Plugin {self.plugin_id}",
            "version": "1.0.0",
            "description": "Mock detection plugin",
        }

    async def analyze(self, listing):
        self.analyze_called = True
        return {"signals": [], "score": 0.5}

    def get_weight(self):
        return self.default_weight

    def shutdown(self):
        self.shutdown_called = True


class TestPluginManagerDetectionIntegration:
    """Test suite for detection plugin registry integration."""

    @pytest.fixture
    def manager(self):
        """Create fresh plugin manager."""
        return PluginManager()

    @pytest.fixture
    def sample_detection_metadata(self):
        """Sample detection plugin metadata."""
        return PluginMetadata(
            id="plugin-detection-price",
            name="Price Anomaly Detector",
            version="1.0.0",
            type="detection",
            enabled=True,
            description="Detects price anomalies",
        )

    def test_get_by_type_detection(self, manager, sample_detection_metadata):
        """Test getting plugins by type."""
        # Register detection plugin
        manager.register(sample_detection_metadata)

        # Register non-detection plugin
        source_plugin = PluginMetadata(
            id="plugin-source-cian",
            name="CIAN Source",
            version="1.0.0",
            type="source",
            enabled=True,
        )
        manager.register(source_plugin)

        # Get detection plugins only
        detection_plugins = manager.get_by_type("detection")

        assert len(detection_plugins) == 1
        assert detection_plugins[0].id == "plugin-detection-price"
        assert detection_plugins[0].type == "detection"

    def test_get_by_type_enabled_filter(self, manager):
        """Test filtering by enabled status."""
        # Register enabled plugin
        enabled_plugin = PluginMetadata(
            id="plugin-detection-enabled",
            name="Enabled Detector",
            version="1.0.0",
            type="detection",
            enabled=True,
        )
        manager.register(enabled_plugin)

        # Register disabled plugin
        disabled_plugin = PluginMetadata(
            id="plugin-detection-disabled",
            name="Disabled Detector",
            version="1.0.0",
            type="detection",
            enabled=False,
        )
        manager.register(disabled_plugin)

        # Get only enabled
        enabled_only = manager.get_by_type("detection", enabled_only=True)
        assert len(enabled_only) == 1
        assert enabled_only[0].id == "plugin-detection-enabled"

        # Get all
        all_plugins = manager.get_by_type("detection", enabled_only=False)
        assert len(all_plugins) == 2

    def test_get_instance(self, manager, sample_detection_metadata):
        """Test getting plugin instance."""
        manager.register(sample_detection_metadata)

        # Store mock instance
        mock_instance = MockDetectionPlugin("plugin-detection-price")
        manager._instances["plugin-detection-price"] = mock_instance

        # Retrieve instance
        instance = manager.get_instance("plugin-detection-price")
        assert instance is mock_instance
        assert instance.plugin_id == "plugin-detection-price"

    def test_get_instance_not_found(self, manager):
        """Test getting non-existent plugin instance."""
        instance = manager.get_instance("non-existent")
        assert instance is None

    def test_get_detection_plugins_unwrapped(self, manager, sample_detection_metadata):
        """Test getting detection plugins without wrapping."""
        manager.register(sample_detection_metadata)

        # Store mock instance
        mock_instance = MockDetectionPlugin("plugin-detection-price")
        manager._instances["plugin-detection-price"] = mock_instance

        # Get plugins without wrapping
        plugins = manager.get_detection_plugins(wrap_with_config=False)

        assert len(plugins) == 1
        assert plugins[0] is mock_instance

    def test_get_detection_plugins_wrapped(self, manager, sample_detection_metadata):
        """Test getting detection plugins with wrapper."""
        manager.register(sample_detection_metadata)

        # Store mock instance
        mock_instance = MockDetectionPlugin("plugin-detection-price", default_weight=0.3)
        manager._instances["plugin-detection-price"] = mock_instance

        # Get plugins with wrapping
        plugins = manager.get_detection_plugins(wrap_with_config=True)

        assert len(plugins) == 1
        assert isinstance(plugins[0], DetectionPluginWrapper)
        assert plugins[0].plugin_id == "plugin-detection-price"

    def test_set_weight(self, manager, sample_detection_metadata):
        """Test setting plugin weight."""
        manager.register(sample_detection_metadata)

        # Set weight
        success = manager.set_weight("plugin-detection-price", 0.8)
        assert success is True

        # Verify weight stored
        weight = manager.get_weight("plugin-detection-price")
        assert weight == 0.8

    def test_set_weight_invalid_range(self, manager, sample_detection_metadata):
        """Test setting invalid weight raises error."""
        manager.register(sample_detection_metadata)

        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            manager.set_weight("plugin-detection-price", 1.5)

        with pytest.raises(ValueError):
            manager.set_weight("plugin-detection-price", -0.1)

    def test_set_weight_not_found(self, manager):
        """Test setting weight for non-existent plugin."""
        success = manager.set_weight("non-existent", 0.5)
        assert success is False

    def test_get_weight_not_configured(self, manager, sample_detection_metadata):
        """Test getting weight when not configured."""
        manager.register(sample_detection_metadata)

        weight = manager.get_weight("plugin-detection-price")
        assert weight is None  # Not configured yet

    def test_enable_disable_affects_detection_list(self, manager, sample_detection_metadata):
        """Test that enable/disable affects detection plugin list."""
        manager.register(sample_detection_metadata)
        mock_instance = MockDetectionPlugin("plugin-detection-price")
        manager._instances["plugin-detection-price"] = mock_instance

        # Initially enabled
        plugins = manager.get_detection_plugins()
        assert len(plugins) == 1

        # Disable plugin
        manager.disable("plugin-detection-price")
        plugins = manager.get_detection_plugins()
        assert len(plugins) == 0  # Should be empty now

        # Re-enable
        manager.enable("plugin-detection-price")
        plugins = manager.get_detection_plugins()
        assert len(plugins) == 1


class TestDetectionPluginWrapper:
    """Test suite for DetectionPluginWrapper."""

    @pytest.fixture
    def mock_plugin(self):
        """Create mock detection plugin."""
        return MockDetectionPlugin("test-plugin", default_weight=0.4)

    def test_wrapper_delegates_metadata(self, mock_plugin):
        """Test wrapper delegates get_metadata to plugin."""
        wrapper = DetectionPluginWrapper(mock_plugin, "test-plugin")

        metadata = wrapper.get_metadata()
        assert metadata["id"] == "test-plugin"
        assert metadata["name"] == "Mock Plugin test-plugin"

    @pytest.mark.asyncio
    async def test_wrapper_delegates_analyze(self, mock_plugin):
        """Test wrapper delegates analyze to plugin."""
        wrapper = DetectionPluginWrapper(mock_plugin, "test-plugin")

        result = await wrapper.analyze({"listing_id": "test"})
        assert mock_plugin.analyze_called is True
        assert "signals" in result

    def test_wrapper_uses_override_weight(self, mock_plugin):
        """Test wrapper uses override weight when configured."""
        wrapper = DetectionPluginWrapper(mock_plugin, "test-plugin", weight_override=0.9)

        # Should use override, not plugin's default (0.4)
        assert wrapper.get_weight() == 0.9

    def test_wrapper_uses_plugin_weight_when_no_override(self, mock_plugin):
        """Test wrapper uses plugin's weight when no override."""
        wrapper = DetectionPluginWrapper(mock_plugin, "test-plugin", weight_override=None)

        # Should use plugin's default weight
        assert wrapper.get_weight() == 0.4

    def test_wrapper_delegates_shutdown(self, mock_plugin):
        """Test wrapper delegates shutdown to plugin."""
        wrapper = DetectionPluginWrapper(mock_plugin, "test-plugin")

        wrapper.shutdown()
        assert mock_plugin.shutdown_called is True

    def test_wrapper_properties(self, mock_plugin):
        """Test wrapper properties."""
        wrapper = DetectionPluginWrapper(mock_plugin, "test-plugin")

        assert wrapper.plugin_id == "test-plugin"
        assert wrapper.wrapped_plugin is mock_plugin


class TestDetectionPluginIntegrationScenarios:
    """Integration test scenarios for detection plugin registry."""

    @pytest.fixture
    def manager_with_plugins(self):
        """Create manager with multiple detection plugins."""
        manager = PluginManager()

        # Plugin 1: High priority, custom weight
        plugin1_meta = PluginMetadata(
            id="plugin-detection-price",
            name="Price Detector",
            version="1.0.0",
            type="detection",
            enabled=True,
            weight=0.8,
        )
        manager.register(plugin1_meta)
        manager._instances["plugin-detection-price"] = MockDetectionPlugin("plugin-detection-price", default_weight=0.5)

        # Plugin 2: Medium priority, no custom weight
        plugin2_meta = PluginMetadata(
            id="plugin-detection-location",
            name="Location Detector",
            version="1.0.0",
            type="detection",
            enabled=True,
        )
        manager.register(plugin2_meta)
        manager._instances["plugin-detection-location"] = MockDetectionPlugin(
            "plugin-detection-location", default_weight=0.3
        )

        # Plugin 3: Disabled
        plugin3_meta = PluginMetadata(
            id="plugin-detection-disabled",
            name="Disabled Detector",
            version="1.0.0",
            type="detection",
            enabled=False,
        )
        manager.register(plugin3_meta)
        manager._instances["plugin-detection-disabled"] = MockDetectionPlugin("plugin-detection-disabled")

        return manager

    def test_scenario_orchestrator_integration(self, manager_with_plugins):
        """Test typical scenario: getting plugins for orchestrator."""
        # Get enabled detection plugins with configured weights
        plugins = manager_with_plugins.get_detection_plugins()

        # Should get 2 plugins (1 disabled)
        assert len(plugins) == 2

        # All should be wrapped
        assert all(isinstance(p, DetectionPluginWrapper) for p in plugins)

        # Check weights
        price_plugin = next(p for p in plugins if p.plugin_id == "plugin-detection-price")
        location_plugin = next(p for p in plugins if p.plugin_id == "plugin-detection-location")

        # Price plugin should use configured weight (0.8), not default (0.5)
        assert price_plugin.get_weight() == 0.8

        # Location plugin should use plugin's default (0.3) since no override
        assert location_plugin.get_weight() == 0.3

    def test_scenario_runtime_weight_change(self, manager_with_plugins):
        """Test changing plugin weight at runtime."""
        # Initial state
        plugins = manager_with_plugins.get_detection_plugins()
        location_plugin = next(p for p in plugins if p.plugin_id == "plugin-detection-location")
        assert location_plugin.get_weight() == 0.3  # Default

        # Change weight
        manager_with_plugins.set_weight("plugin-detection-location", 0.7)

        # Get plugins again (new wrapper instances)
        plugins = manager_with_plugins.get_detection_plugins()
        location_plugin = next(p for p in plugins if p.plugin_id == "plugin-detection-location")

        # Should use new weight
        assert location_plugin.get_weight() == 0.7

    def test_scenario_enable_disable_workflow(self, manager_with_plugins):
        """Test enable/disable workflow."""
        # Initially 2 enabled
        plugins = manager_with_plugins.get_detection_plugins()
        assert len(plugins) == 2

        # Disable one
        manager_with_plugins.disable("plugin-detection-price")
        plugins = manager_with_plugins.get_detection_plugins()
        assert len(plugins) == 1
        assert plugins[0].plugin_id == "plugin-detection-location"

        # Enable the disabled one
        manager_with_plugins.enable("plugin-detection-disabled")
        plugins = manager_with_plugins.get_detection_plugins()
        assert len(plugins) == 2
        plugin_ids = {p.plugin_id for p in plugins}
        assert "plugin-detection-location" in plugin_ids
        assert "plugin-detection-disabled" in plugin_ids
