"""Tests for plugin interface contracts.

This test suite validates that:
1. All abstract methods are properly enforced
2. Test plugins implement all required interface methods
3. Interface contracts are properly validated
4. Inheritance and method signatures are correct
"""

import inspect
from abc import ABC
from typing import get_type_hints

import pytest

from core.interfaces.detection_plugin import DetectionPlugin, DetectionResult
from core.interfaces.processing_plugin import ProcessingPlugin
from core.interfaces.source_plugin import SourcePlugin
from tests.fixtures.plugins.test_detection_plugin.detector import TestDetectionPlugin
from tests.fixtures.plugins.test_processing_plugin.processor import (
    TestProcessingPlugin,
)
from tests.fixtures.plugins.test_source_plugin.cian_plugin import CianSourcePlugin

pytestmark = [pytest.mark.unit, pytest.mark.plugins]


class TestSourcePluginContract:
    """Test SourcePlugin interface contract."""

    def test_source_plugin_is_abstract(self):
        """Test that SourcePlugin is an abstract base class."""
        assert issubclass(SourcePlugin, ABC)
        assert SourcePlugin.__abstractmethods__

    def test_source_plugin_required_methods(self):
        """Test that SourcePlugin defines all required abstract methods."""
        required_methods = {
            "get_metadata",
            "configure",
            "validate_config",
            "scrape",
            "scrape_single",
            "validate_listing",
            "get_statistics",
        }

        abstract_methods = {
            name
            for name, method in inspect.getmembers(SourcePlugin, inspect.isfunction)
            if getattr(method, "__isabstractmethod__", False)
        }

        assert required_methods == abstract_methods, (
            f"Missing abstract methods: {required_methods - abstract_methods}, "
            f"Extra abstract methods: {abstract_methods - required_methods}"
        )

    def test_source_plugin_cannot_instantiate(self):
        """Test that SourcePlugin cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            SourcePlugin()  # type: ignore

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementations fail to instantiate."""

        class IncompleteSource(SourcePlugin):
            """Missing most required methods."""

            def get_metadata(self):
                return {}

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteSource()  # type: ignore

    def test_test_source_plugin_implements_all_methods(self):
        """Test that CianSourcePlugin implements all required methods."""
        plugin = CianSourcePlugin()

        # Verify all abstract methods are implemented
        for method_name in SourcePlugin.__abstractmethods__:
            assert hasattr(plugin, method_name), f"Missing method: {method_name}"
            method = getattr(plugin, method_name)
            assert callable(method), f"{method_name} is not callable"

    def test_test_source_plugin_method_signatures(self):
        """Test that CianSourcePlugin methods have correct signatures."""
        plugin = CianSourcePlugin()

        # Test get_metadata signature
        metadata = plugin.get_metadata()
        assert isinstance(metadata, dict)

        # Test configure signature
        plugin.configure({"key": "value"})

        # Test validate_config signature
        result = plugin.validate_config()
        assert isinstance(result, bool)

        # Test scrape signature
        listings = list(plugin.scrape({}))
        assert isinstance(listings, list)

        # Test scrape_single signature
        listing = plugin.scrape_single("test-id")
        assert listing is None or isinstance(listing, dict)

        # Test validate_listing signature
        is_valid = plugin.validate_listing({"id": "test"})
        assert isinstance(is_valid, bool)

        # Test get_statistics signature
        stats = plugin.get_statistics()
        assert isinstance(stats, dict)

    def test_source_plugin_optional_shutdown(self):
        """Test that shutdown method is optional with default implementation."""
        plugin = CianSourcePlugin()

        # Should have shutdown method
        assert hasattr(plugin, "shutdown")
        assert callable(plugin.shutdown)

        # Should not raise when called
        plugin.shutdown()


class TestProcessingPluginContract:
    """Test ProcessingPlugin interface contract."""

    def test_processing_plugin_is_abstract(self):
        """Test that ProcessingPlugin is an abstract base class."""
        assert issubclass(ProcessingPlugin, ABC)
        assert ProcessingPlugin.__abstractmethods__

    def test_processing_plugin_required_methods(self):
        """Test that ProcessingPlugin defines all required abstract methods."""
        required_methods = {"get_metadata", "process", "get_priority"}

        abstract_methods = {
            name
            for name, method in inspect.getmembers(ProcessingPlugin, inspect.isfunction)
            if getattr(method, "__isabstractmethod__", False)
        }

        assert required_methods == abstract_methods

    def test_processing_plugin_cannot_instantiate(self):
        """Test that ProcessingPlugin cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ProcessingPlugin()  # type: ignore

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementations fail to instantiate."""

        class IncompleteProcessing(ProcessingPlugin):
            """Missing required methods."""

            def get_metadata(self):
                return {}

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteProcessing()  # type: ignore

    def test_test_processing_plugin_implements_all_methods(self):
        """Test that TestProcessingPlugin implements all required methods."""
        plugin = TestProcessingPlugin()

        # Verify all abstract methods are implemented
        for method_name in ProcessingPlugin.__abstractmethods__:
            assert hasattr(plugin, method_name), f"Missing method: {method_name}"
            method = getattr(plugin, method_name)
            assert callable(method), f"{method_name} is not callable"

    def test_test_processing_plugin_method_signatures(self):
        """Test that TestProcessingPlugin methods have correct signatures."""
        plugin = TestProcessingPlugin()

        # Test get_metadata signature
        metadata = plugin.get_metadata()
        assert isinstance(metadata, dict)

        # Test process signature
        listing = {"id": "test", "price": 1000}
        result = plugin.process(listing)
        assert isinstance(result, dict)

        # Test get_priority signature
        priority = plugin.get_priority()
        assert isinstance(priority, int)

    def test_processing_plugin_optional_shutdown(self):
        """Test that shutdown method is optional with default implementation."""
        plugin = TestProcessingPlugin()

        # Should have shutdown method
        assert hasattr(plugin, "shutdown")
        assert callable(plugin.shutdown)

        # Should not raise when called
        plugin.shutdown()


class TestDetectionPluginContract:
    """Test DetectionPlugin interface contract."""

    def test_detection_plugin_is_abstract(self):
        """Test that DetectionPlugin is an abstract base class."""
        assert issubclass(DetectionPlugin, ABC)
        assert DetectionPlugin.__abstractmethods__

    def test_detection_plugin_required_methods(self):
        """Test that DetectionPlugin defines all required abstract methods."""
        required_methods = {"get_metadata", "analyze", "get_weight"}

        abstract_methods = {
            name
            for name, method in inspect.getmembers(DetectionPlugin, inspect.isfunction)
            if getattr(method, "__isabstractmethod__", False)
        }

        assert required_methods == abstract_methods

    def test_detection_plugin_cannot_instantiate(self):
        """Test that DetectionPlugin cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            DetectionPlugin()  # type: ignore

    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementations fail to instantiate."""

        class IncompleteDetection(DetectionPlugin):
            """Missing required methods."""

            def get_metadata(self):
                return {}

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteDetection()  # type: ignore

    def test_test_detection_plugin_implements_all_methods(self):
        """Test that TestDetectionPlugin implements all required methods."""
        plugin = TestDetectionPlugin()

        # Verify all abstract methods are implemented
        for method_name in DetectionPlugin.__abstractmethods__:
            assert hasattr(plugin, method_name), f"Missing method: {method_name}"
            method = getattr(plugin, method_name)
            assert callable(method), f"{method_name} is not callable"

    @pytest.mark.asyncio
    async def test_test_detection_plugin_method_signatures(self):
        """Test that TestDetectionPlugin methods have correct signatures."""
        plugin = TestDetectionPlugin()

        # Test get_metadata signature
        metadata = plugin.get_metadata()
        assert isinstance(metadata, dict)

        # Test analyze signature
        listing = {"id": "test", "price": 1000}
        result = await plugin.analyze(listing)
        assert isinstance(result, DetectionResult)
        assert result.plugin_id == "plugin-detection-test"
        assert isinstance(result.signals, list)
        assert isinstance(result.overall_score, float)
        assert 0.0 <= result.overall_score <= 1.0
        assert isinstance(result.processing_time_ms, float)
        assert result.processing_time_ms >= 0.0

        # Test get_weight signature
        weight = plugin.get_weight()
        assert isinstance(weight, float)
        assert 0.0 <= weight <= 1.0

    def test_detection_plugin_optional_shutdown(self):
        """Test that shutdown method is optional with default implementation."""
        plugin = TestDetectionPlugin()

        # Should have shutdown method
        assert hasattr(plugin, "shutdown")
        assert callable(plugin.shutdown)

        # Should not raise when called
        plugin.shutdown()


class TestInterfaceInheritance:
    """Test interface inheritance and relationships."""

    def test_all_plugins_inherit_from_abc(self):
        """Test that all plugin interfaces inherit from ABC."""
        assert issubclass(SourcePlugin, ABC)
        assert issubclass(ProcessingPlugin, ABC)
        assert issubclass(DetectionPlugin, ABC)

    def test_test_plugins_inherit_from_interfaces(self):
        """Test that test plugins properly inherit from their interfaces."""
        assert issubclass(CianSourcePlugin, SourcePlugin)
        assert issubclass(TestProcessingPlugin, ProcessingPlugin)
        assert issubclass(TestDetectionPlugin, DetectionPlugin)

    def test_test_plugins_are_instances(self):
        """Test that test plugin instances are proper instances."""
        source = CianSourcePlugin()
        processing = TestProcessingPlugin()
        detection = TestDetectionPlugin()

        assert isinstance(source, SourcePlugin)
        assert isinstance(processing, ProcessingPlugin)
        assert isinstance(detection, DetectionPlugin)


class TestInterfaceMethodCoverage:
    """Test that all interface methods are exercised by test plugins."""

    def test_source_plugin_all_methods_callable(self):
        """Test that all SourcePlugin methods can be called without errors."""
        plugin = CianSourcePlugin()

        # Call all methods
        plugin.get_metadata()
        plugin.configure({"test": "config"})
        plugin.validate_config()
        list(plugin.scrape({}))
        plugin.scrape_single("test-id")
        plugin.validate_listing({"id": "test"})
        plugin.get_statistics()
        plugin.shutdown()

    def test_processing_plugin_all_methods_callable(self):
        """Test that all ProcessingPlugin methods can be called without errors."""
        plugin = TestProcessingPlugin()

        # Call all methods
        plugin.get_metadata()
        plugin.process({"id": "test"})
        plugin.get_priority()
        plugin.shutdown()

    @pytest.mark.asyncio
    async def test_detection_plugin_all_methods_callable(self):
        """Test that all DetectionPlugin methods can be called without errors."""
        plugin = TestDetectionPlugin()

        # Call all methods
        plugin.get_metadata()
        await plugin.analyze({"id": "test"})
        plugin.get_weight()
        plugin.shutdown()


class TestInterfaceDocumentation:
    """Test that interfaces are properly documented."""

    def test_source_plugin_has_docstrings(self):
        """Test that SourcePlugin has docstrings."""
        assert SourcePlugin.__doc__ is not None
        assert SourcePlugin.shutdown.__doc__ is not None

    def test_processing_plugin_has_docstrings(self):
        """Test that ProcessingPlugin has docstrings."""
        assert ProcessingPlugin.__doc__ is not None
        assert ProcessingPlugin.shutdown.__doc__ is not None

    def test_detection_plugin_has_docstrings(self):
        """Test that DetectionPlugin has docstrings."""
        assert DetectionPlugin.__doc__ is not None
        assert DetectionPlugin.analyze.__doc__ is not None
        assert DetectionPlugin.shutdown.__doc__ is not None


class TestShutdownHook:
    """Test shutdown hook behavior across all interfaces."""

    def test_shutdown_is_optional(self):
        """Test that shutdown has default implementation in all interfaces."""
        # Source plugin
        source = CianSourcePlugin()
        source.shutdown()  # Should not raise

        # Processing plugin
        processing = TestProcessingPlugin()
        processing.shutdown()  # Should not raise

        # Detection plugin
        detection = TestDetectionPlugin()
        detection.shutdown()  # Should not raise

    def test_shutdown_can_be_overridden(self):
        """Test that shutdown can be customized."""

        class CustomSource(SourcePlugin):
            def __init__(self):
                self.shutdown_called = False

            def get_metadata(self):
                return {}

            def configure(self, config):
                pass

            def validate_config(self):
                return True

            def scrape(self, params):
                yield {}

            def scrape_single(self, listing_id):
                return None

            def validate_listing(self, listing):
                return True

            def get_statistics(self):
                return {}

            def shutdown(self):
                self.shutdown_called = True

        plugin = CustomSource()
        assert not plugin.shutdown_called
        plugin.shutdown()
        assert plugin.shutdown_called
