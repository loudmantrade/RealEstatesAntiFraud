"""Integration tests for plugin test fixtures."""

import pytest

from tests.fixtures.plugins.test_dependent_plugin import TestDependentPlugin
from tests.fixtures.plugins.test_detection_plugin import TestDetectionPlugin
from tests.fixtures.plugins.test_processing_plugin import TestProcessingPlugin


class TestPluginFixtures:
    """Test suite for plugin test fixtures."""

    @pytest.mark.asyncio
    async def test_processing_plugin_basic(self):
        """Test basic processing plugin functionality."""
        plugin = TestProcessingPlugin({"price_multiplier": 1.5})

        listing = {"id": "123", "price": 1000000}
        result = await plugin.process(listing)

        assert result["price_normalized"] == 1500000
        assert result["processed"] is True
        assert result["metadata"]["processed_by"] == "plugin-processing-test"

    @pytest.mark.asyncio
    async def test_processing_plugin_metadata(self):
        """Test processing plugin metadata."""
        plugin = TestProcessingPlugin()

        metadata = plugin.get_metadata()

        assert metadata["id"] == "plugin-processing-test"
        assert metadata["type"] == "processing"
        assert "price_normalization" in metadata["capabilities"]
        assert metadata["processed_count"] == 0

    @pytest.mark.asyncio
    async def test_processing_plugin_without_metadata(self):
        """Test processing plugin with add_metadata=False."""
        plugin = TestProcessingPlugin({"add_metadata": False})

        listing = {"id": "123", "price": 1000000}
        result = await plugin.process(listing)

        assert "metadata" not in result or "processed_by" not in result.get(
            "metadata", {}
        )

    @pytest.mark.asyncio
    async def test_detection_plugin_price_anomaly(self):
        """Test detection plugin identifies price anomalies."""
        plugin = TestDetectionPlugin({"price_threshold_multiplier": 2.0})

        # High price (exceeds threshold)
        listing = {"id": "123", "price": 15000000}
        result = await plugin.analyze(listing)

        assert len(result.signals) > 0
        assert result.signals[0].signal_type == "price_anomaly"
        assert result.overall_score > 0.0

    @pytest.mark.asyncio
    async def test_detection_plugin_duplicate_detection(self):
        """Test detection plugin identifies duplicates."""
        plugin = TestDetectionPlugin({"enable_duplicate_check": True})

        listing1 = {"id": "123", "price": 1000000}
        listing2 = {"id": "123", "price": 1000000}

        # First occurrence - no duplicate signal
        result1 = await plugin.analyze(listing1)
        duplicate_signals = [
            s for s in result1.signals if s.signal_type == "duplicate_listing"
        ]
        assert len(duplicate_signals) == 0

        # Second occurrence - duplicate signal
        result2 = await plugin.analyze(listing2)
        duplicate_signals = [
            s for s in result2.signals if s.signal_type == "duplicate_listing"
        ]
        assert len(duplicate_signals) == 1
        assert result2.overall_score > 0.0

    @pytest.mark.asyncio
    async def test_detection_plugin_metadata(self):
        """Test detection plugin metadata."""
        plugin = TestDetectionPlugin()

        metadata = plugin.get_metadata()

        assert metadata["id"] == "plugin-detection-test"
        assert metadata["type"] == "detection"
        assert "price_anomaly_detection" in metadata["capabilities"]

    @pytest.mark.asyncio
    async def test_dependent_plugin_with_normalized_price(self):
        """Test dependent plugin uses normalized price."""
        dependent = TestDependentPlugin({"use_normalization": True})

        # Simulate processed listing with normalized price
        listing = {
            "id": "123",
            "price": 1000000,
            "price_normalized": 1500000,
            "metadata": {"processed_by": "plugin-processing-test"},
        }

        result = await dependent.process(listing)

        assert result["enriched"] is True
        assert result["price_final"] == 1500000  # Uses normalized price
        assert result["metadata"]["enriched_by"] == "plugin-dependent-test"
        assert result["metadata"]["used_normalization"] is True

    @pytest.mark.asyncio
    async def test_dependent_plugin_metadata(self):
        """Test dependent plugin metadata."""
        plugin = TestDependentPlugin()

        metadata = plugin.get_metadata()

        assert metadata["id"] == "plugin-dependent-test"
        assert metadata["type"] == "processing"
        assert "plugin-processing-test" in metadata["dependencies"]
        assert "plugin-detection-test" in metadata["dependencies"]

    @pytest.mark.asyncio
    async def test_plugin_shutdown(self):
        """Test plugin shutdown resets state."""
        plugin = TestProcessingPlugin()

        # Process some listings
        await plugin.process({"id": "1", "price": 1000})
        await plugin.process({"id": "2", "price": 2000})
        assert plugin.processed_count == 2

        # Shutdown should reset
        plugin.shutdown()
        assert plugin.processed_count == 0


class TestPluginTestHelper:
    """Test suite for PluginTestHelper utility."""

    def test_helper_copy_plugin_fixture(self, plugin_test_helper):
        """Test copying plugin fixtures."""
        plugin_dir = plugin_test_helper.copy_plugin_fixture("test_processing_plugin")

        assert plugin_dir.exists()
        assert (plugin_dir / "plugin.yaml").exists()
        assert (plugin_dir / "processor.py").exists()
        assert (plugin_dir / "__init__.py").exists()

    def test_helper_create_plugin_dir(self, plugin_test_helper):
        """Test creating plugin directory."""
        plugin_dir = plugin_test_helper.create_plugin_dir(
            plugin_id="test-plugin",
            plugin_name="Test Plugin",
            plugin_type="processing",
            entrypoint="processor.TestProcessor",
            capabilities=["test_capability"],
        )

        assert plugin_dir.exists()
        assert (plugin_dir / "plugin.yaml").exists()

        manifest = plugin_test_helper.read_manifest(plugin_dir)
        assert manifest["id"] == "test-plugin"
        assert manifest["type"] == "processing"
        assert "test_capability" in manifest["capabilities"]

    def test_helper_list_plugins(self, plugin_test_helper):
        """Test listing plugins."""
        # Create some plugins
        plugin_test_helper.create_plugin_dir(
            plugin_id="plugin-1",
            plugin_name="Plugin 1",
            plugin_type="processing",
            entrypoint="p1.Plugin1",
        )
        plugin_test_helper.create_plugin_dir(
            plugin_id="plugin-2",
            plugin_name="Plugin 2",
            plugin_type="detection",
            entrypoint="p2.Plugin2",
        )

        plugins = plugin_test_helper.list_plugins()
        assert len(plugins) == 2

    def test_helper_context_manager(self, tmp_path):
        """Test helper as context manager with automatic cleanup."""
        from tests.integration.plugin_utils import PluginTestHelper

        plugin_dir = None
        with PluginTestHelper(tmp_path) as helper:
            plugin_dir = helper.create_plugin_dir(
                plugin_id="test-plugin",
                plugin_name="Test Plugin",
                plugin_type="processing",
                entrypoint="test.Plugin",
            )
            assert plugin_dir.exists()

        # After context, cleanup should have happened
        assert not plugin_dir.exists()


class TestPluginPytestFixtures:
    """Test suite for pytest fixtures."""

    def test_plugin_fixtures_dir(self, plugin_fixtures_dir):
        """Test plugin_fixtures_dir fixture."""
        assert plugin_fixtures_dir.exists()
        assert (plugin_fixtures_dir / "test_processing_plugin").exists()
        assert (plugin_fixtures_dir / "test_detection_plugin").exists()

    def test_sample_plugins(self, sample_plugins):
        """Test sample_plugins fixture."""
        assert "processing" in sample_plugins
        assert "detection" in sample_plugins
        assert "dependent" in sample_plugins
        assert "source" in sample_plugins

        # Verify they exist
        for name, path in sample_plugins.items():
            assert path.exists(), f"Plugin {name} path does not exist"
            assert (path / "plugin.yaml").exists(), f"Plugin {name} has no manifest"
