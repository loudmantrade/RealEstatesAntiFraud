# Plugin Testing Guide

This document provides comprehensive guidance on testing plugins in the RealEstatesAntiFraud system.

## Table of Contents

- [Overview](#overview)
- [Test Plugin Fixtures](#test-plugin-fixtures)
- [Plugin Test Helper](#plugin-test-helper)
- [Pytest Fixtures](#pytest-fixtures)
- [Writing Plugin Tests](#writing-plugin-tests)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The plugin testing infrastructure provides comprehensive tools for integration testing of the plugin system. It includes:

- **Test Plugin Fixtures**: Ready-to-use plugin implementations for testing
- **PluginTestHelper**: Utility class for managing test plugins
- **Pytest Fixtures**: Pre-configured fixtures for plugin testing
- **Integration Tests**: End-to-end testing with real plugin loading

### Test Environment

Plugin tests run in an isolated environment with:
- Temporary plugin directories (pytest `tmp_path`)
- Clean plugin manager instances
- Isolated configuration
- Automatic cleanup after tests

## Test Plugin Fixtures

The system includes several pre-built test plugins located in `tests/fixtures/plugins/`:

### 1. Test Processing Plugin

**Location**: `tests/fixtures/plugins/test_processing_plugin/`

**Purpose**: Processing plugin for data transformation and enrichment.

**Capabilities**:
- `price_normalization` - Normalize prices with configurable multiplier
- `data_enrichment` - Add processing metadata

**Configuration**:
```yaml
price_multiplier: 1.0  # Float multiplier for price normalization
add_metadata: true     # Boolean to add processing metadata
```

**Usage Example**:
```python
from tests.fixtures.plugins.test_processing_plugin import TestProcessingPlugin

# Initialize with config
plugin = TestProcessingPlugin({
    "price_multiplier": 1.5,
    "add_metadata": True
})

# Process a listing
listing = {"id": "123", "price": 1000000}
result = await plugin.process(listing)

# Result includes normalized price and metadata
assert result["price_normalized"] == 1500000
assert result["processed"] is True
assert result["metadata"]["processed_by"] == "plugin-processing-test"
```

### 2. Test Detection Plugin

**Location**: `tests/fixtures/plugins/test_detection_plugin/`

**Purpose**: Detection plugin for fraud signal identification.

**Capabilities**:
- `price_anomaly_detection` - Detect unrealistic prices
- `basic_fraud_signals` - Generate fraud risk signals

**Configuration**:
```yaml
price_threshold_multiplier: 2.0  # Multiplier for price anomaly threshold
enable_duplicate_check: true     # Enable duplicate listing detection
```

**Usage Example**:
```python
from tests.fixtures.plugins.test_detection_plugin import TestDetectionPlugin

# Initialize with config
plugin = TestDetectionPlugin({
    "price_threshold_multiplier": 2.0,
    "enable_duplicate_check": True
})

# Analyze a listing
listing = {"id": "123", "price": 15000000}  # High price
result = await plugin.analyze(listing)

# Result includes risk signals
assert len(result.signals) > 0
assert result.signals[0].signal_type == "price_anomaly"
assert result.overall_score > 0.0
```

### 3. Test Dependent Plugin

**Location**: `tests/fixtures/plugins/test_dependent_plugin/`

**Purpose**: Plugin that depends on other plugins for dependency testing.

**Dependencies**:
- `plugin-processing-test`
- `plugin-detection-test`

**Capabilities**:
- `enriched_processing` - Process with dependency data
- `dependent_processing` - Demonstrate dependency handling

**Configuration**:
```yaml
use_normalization: true  # Use normalized prices from processing plugin
```

**Usage Example**:
```python
# This plugin requires other plugins to be loaded first
# PluginManager handles dependency resolution automatically

# Plugins are loaded in dependency order:
# 1. plugin-processing-test (no dependencies)
# 2. plugin-detection-test (no dependencies)
# 3. plugin-dependent-test (depends on above)

listing = {"id": "123", "price": 1000000}

# First process with processing plugin
processed = await processing_plugin.process(listing)

# Then use dependent plugin (uses normalized price)
enriched = await dependent_plugin.process(processed)

assert enriched["enriched"] is True
assert enriched["price_final"] == processed["price_normalized"]
```

### 4. Test Source Plugin

**Location**: `tests/fixtures/plugins/test_source_plugin/`

**Purpose**: Source plugin for testing data fetching (existing fixture).

## Plugin Test Helper

The `PluginTestHelper` class provides utilities for managing test plugins.

**Location**: `tests/integration/plugin_utils.py`

### Creating a Helper Instance

```python
from tests.integration.plugin_utils import PluginTestHelper

def test_plugin(tmp_path):
    helper = PluginTestHelper(tmp_path)
    # ... use helper ...
    helper.cleanup()
```

Or use as a context manager:

```python
def test_plugin(tmp_path):
    with PluginTestHelper(tmp_path) as helper:
        # ... use helper ...
        pass  # Automatic cleanup
```

### Key Methods

#### Copy Plugin Fixture

Copy an existing plugin fixture to the test directory:

```python
plugin_dir = helper.copy_plugin_fixture("test_processing_plugin")
# Plugin is now in tmp_path/test_processing_plugin/
```

#### Create Plugin Directory

Create a new plugin programmatically:

```python
plugin_dir = helper.create_plugin_dir(
    plugin_id="custom-test-plugin",
    plugin_name="Custom Test Plugin",
    plugin_type="processing",
    entrypoint="processor.CustomPlugin",
    version="1.0.0",
    capabilities=["custom_processing"],
    configuration={
        "setting": {
            "type": "string",
            "default": "value"
        }
    }
)
```

#### Create Plugin File

Add a Python file to a plugin:

```python
content = '''
from core.interfaces.processing_plugin import ProcessingPlugin

class CustomPlugin(ProcessingPlugin):
    async def process(self, listing):
        return listing
    
    def get_metadata(self):
        return {"id": "custom-test-plugin"}
    
    def get_weight(self):
        return 1.0
'''

helper.create_plugin_file(plugin_dir, "processor.py", content)
```

#### List Plugins

Get all plugin directories in the test environment:

```python
plugins = helper.list_plugins()
for plugin_dir in plugins:
    manifest = helper.read_manifest(plugin_dir)
    print(f"Found plugin: {manifest['id']}")
```

## Pytest Fixtures

Integration test fixtures are defined in `tests/integration/conftest.py`.

### plugin_test_helper

Provides a `PluginTestHelper` instance with automatic cleanup:

```python
def test_plugin_creation(plugin_test_helper):
    plugin_dir = plugin_test_helper.create_plugin_dir(
        plugin_id="test-plugin",
        plugin_name="Test Plugin",
        plugin_type="processing",
        entrypoint="plugin.TestPlugin"
    )
    assert (plugin_dir / "plugin.yaml").exists()
```

### plugin_fixtures_dir

Provides the path to the plugin fixtures directory:

```python
def test_fixture_exists(plugin_fixtures_dir):
    processing_plugin = plugin_fixtures_dir / "test_processing_plugin"
    assert processing_plugin.exists()
    assert (processing_plugin / "plugin.yaml").exists()
```

### sample_plugins

Copies common test plugins to the test directory:

```python
def test_with_samples(sample_plugins):
    # sample_plugins is a dict with keys:
    # "processing", "detection", "dependent", "source"
    
    processing_dir = sample_plugins["processing"]
    detection_dir = sample_plugins["detection"]
    
    assert (processing_dir / "plugin.yaml").exists()
    assert (detection_dir / "plugin.yaml").exists()
```

### plugin_manager_with_fixtures

Provides a fully initialized `PluginManager` with test plugins loaded:

```python
async def test_plugin_loading(plugin_manager_with_fixtures):
    manager = plugin_manager_with_fixtures
    
    # Plugins are already discovered and loaded
    plugins = manager.get_all_plugins()
    assert len(plugins) > 0
    
    # Get specific plugin
    processing = manager.get_plugin("plugin-processing-test")
    assert processing is not None
    
    # Use plugin
    listing = {"id": "123", "price": 1000000}
    result = await processing.process(listing)
    assert result["processed"] is True
```

## Writing Plugin Tests

### Basic Plugin Test

```python
import pytest
from tests.fixtures.plugins.test_processing_plugin import TestProcessingPlugin

@pytest.mark.asyncio
async def test_processing_plugin():
    """Test basic processing plugin functionality."""
    plugin = TestProcessingPlugin({"price_multiplier": 2.0})
    
    listing = {"id": "123", "price": 1000000}
    result = await plugin.process(listing)
    
    assert result["price_normalized"] == 2000000
    assert result["processed"] is True
```

### Test with Plugin Manager

```python
async def test_plugin_manager_integration(plugin_manager_with_fixtures):
    """Test plugins through plugin manager."""
    manager = plugin_manager_with_fixtures
    
    # Get plugin
    plugin = manager.get_plugin("plugin-processing-test")
    assert plugin is not None
    
    # Verify metadata
    metadata = plugin.get_metadata()
    assert metadata["type"] == "processing"
    
    # Use plugin
    listing = {"id": "123", "price": 1000000}
    result = await plugin.process(listing)
    assert "price_normalized" in result
```

### Test Plugin Discovery

```python
def test_plugin_discovery(plugin_test_helper, tmp_path):
    """Test plugin discovery from directory."""
    from core.plugin_manager import PluginManager
    
    # Copy test plugins
    plugin_test_helper.copy_plugin_fixture("test_processing_plugin")
    plugin_test_helper.copy_plugin_fixture("test_detection_plugin")
    
    # Create plugin manager
    manager = PluginManager(plugin_dirs=[tmp_path])
    
    # Discover plugins
    await manager.discover_plugins()
    
    # Verify discovery
    plugins = manager.get_all_plugins()
    assert len(plugins) >= 2
    
    plugin_ids = [p.get_metadata()["id"] for p in plugins]
    assert "plugin-processing-test" in plugin_ids
    assert "plugin-detection-test" in plugin_ids
```

### Test Plugin Dependencies

```python
async def test_plugin_dependencies(plugin_manager_with_fixtures):
    """Test plugin dependency resolution."""
    manager = plugin_manager_with_fixtures
    
    # Get dependent plugin (requires other plugins)
    dependent = manager.get_plugin("plugin-dependent-test")
    assert dependent is not None
    
    # Verify dependencies loaded first
    metadata = dependent.get_metadata()
    assert "dependencies" in metadata
    
    # Verify can use dependent plugin
    listing = {"id": "123", "price": 1000000}
    
    # Process with dependency chain
    processing = manager.get_plugin("plugin-processing-test")
    processed = await processing.process(listing)
    
    enriched = await dependent.process(processed)
    assert enriched["enriched"] is True
```

### Test Custom Plugin Creation

```python
async def test_custom_plugin(plugin_test_helper):
    """Test creating and using a custom plugin."""
    # Create plugin directory
    plugin_dir = plugin_test_helper.create_plugin_dir(
        plugin_id="custom-processor",
        plugin_name="Custom Processor",
        plugin_type="processing",
        entrypoint="processor.CustomProcessor",
    )
    
    # Create plugin implementation
    code = '''
from core.interfaces.processing_plugin import ProcessingPlugin

class CustomProcessor(ProcessingPlugin):
    async def process(self, listing):
        listing["custom_processed"] = True
        return listing
    
    def get_metadata(self):
        return {"id": "custom-processor", "type": "processing"}
    
    def get_weight(self):
        return 1.0
'''
    plugin_test_helper.create_plugin_file(plugin_dir, "processor.py", code)
    
    # Load and test plugin
    from core.plugin_manager import PluginManager
    manager = PluginManager(plugin_dirs=[plugin_dir.parent])
    await manager.discover_plugins()
    
    plugin = manager.get_plugin("custom-processor")
    assert plugin is not None
    
    listing = {"id": "123"}
    result = await plugin.process(listing)
    assert result["custom_processed"] is True
```

## Best Practices

### 1. Use Fixtures for Common Setups

Always use pytest fixtures for plugin setup to ensure proper cleanup:

```python
@pytest.fixture
def configured_plugin():
    plugin = TestProcessingPlugin({"price_multiplier": 1.5})
    yield plugin
    plugin.shutdown()

async def test_plugin(configured_plugin):
    result = await configured_plugin.process({"price": 1000})
    assert result["price_normalized"] == 1500
```

### 2. Test Plugin Isolation

Ensure plugins don't affect each other between tests:

```python
async def test_plugin_isolation_1(plugin_manager_with_fixtures):
    manager = plugin_manager_with_fixtures
    plugin = manager.get_plugin("plugin-detection-test")
    
    # Process listing
    await plugin.analyze({"id": "123", "price": 1000000})
    
    # Don't rely on state persisting to next test

async def test_plugin_isolation_2(plugin_manager_with_fixtures):
    manager = plugin_manager_with_fixtures
    plugin = manager.get_plugin("plugin-detection-test")
    
    # Plugin state should be clean (new instance)
    assert plugin.analysis_count == 0
```

### 3. Test Error Handling

Test how plugins handle invalid inputs:

```python
async def test_plugin_error_handling():
    plugin = TestProcessingPlugin()
    
    # Test with None price
    result = await plugin.process({"id": "123", "price": None})
    assert "price_normalized" not in result
    
    # Test with missing fields
    result = await plugin.process({})
    assert result["processed"] is True
```

### 4. Test Plugin Configuration

Verify configuration is properly applied:

```python
@pytest.mark.parametrize("multiplier,expected", [
    (1.0, 1000000),
    (1.5, 1500000),
    (2.0, 2000000),
])
async def test_plugin_configuration(multiplier, expected):
    plugin = TestProcessingPlugin({"price_multiplier": multiplier})
    
    listing = {"id": "123", "price": 1000000}
    result = await plugin.process(listing)
    
    assert result["price_normalized"] == expected
```

### 5. Test Plugin Lifecycle

Test plugin initialization and shutdown:

```python
async def test_plugin_lifecycle():
    # Initialize
    plugin = TestProcessingPlugin()
    assert plugin.processed_count == 0
    
    # Use
    await plugin.process({"id": "1", "price": 1000})
    await plugin.process({"id": "2", "price": 2000})
    assert plugin.processed_count == 2
    
    # Shutdown
    plugin.shutdown()
    assert plugin.processed_count == 0
```

## Troubleshooting

### Plugin Not Found

**Problem**: `PluginManager` can't find test plugins.

**Solution**:
```python
# Verify plugin directory exists
assert (tmp_path / "test_processing_plugin").exists()

# Verify manifest exists
assert (tmp_path / "test_processing_plugin" / "plugin.yaml").exists()

# Check plugin_dirs parameter
manager = PluginManager(plugin_dirs=[tmp_path])  # Correct
# NOT: plugin_dirs=[tmp_path / "test_processing_plugin"]  # Wrong
```

### Import Errors

**Problem**: Cannot import plugin classes.

**Solution**:
```python
# Ensure __init__.py exists in plugin directory
assert (plugin_dir / "__init__.py").exists()

# Check entrypoint format in plugin.yaml
# Correct: entrypoint: "processor.TestProcessingPlugin"
# Wrong: entrypoint: "TestProcessingPlugin"
```

### Dependency Errors

**Problem**: Plugin dependencies not resolved.

**Solution**:
```python
# Ensure all dependencies are in plugin_dirs
manager = PluginManager(plugin_dirs=[
    tmp_path / "test_processing_plugin",
    tmp_path / "test_detection_plugin",
    tmp_path / "test_dependent_plugin",  # Depends on above
])

# Or use parent directory
manager = PluginManager(plugin_dirs=[tmp_path])
```

### Async/Await Issues

**Problem**: `RuntimeError: no running event loop`

**Solution**:
```python
# Use pytest.mark.asyncio decorator
@pytest.mark.asyncio
async def test_plugin():
    plugin = TestProcessingPlugin()
    result = await plugin.process({"id": "123"})
    assert result is not None
```

### Cleanup Issues

**Problem**: Plugin state persists between tests.

**Solution**:
```python
# Use function-scoped fixtures
@pytest.fixture
async def clean_manager(tmp_path):
    manager = PluginManager(plugin_dirs=[tmp_path])
    await manager.discover_plugins()
    yield manager
    await manager.shutdown_all()  # Cleanup

# Or use context manager
async def test_plugin(tmp_path):
    with PluginTestHelper(tmp_path) as helper:
        # ... test code ...
        pass  # Auto cleanup
```

## See Also

- [Plugin Development Guide](PLUGIN_DEVELOPMENT.md) - How to create new plugins
- [Plugin Specification](PLUGIN_SPEC.md) - Plugin manifest format
- [Redis Testing Guide](REDIS_TESTING.md) - Testing with Redis
- [Core Development Plan](CORE_DEVELOPMENT_PLAN.md) - System architecture

## Summary

The plugin testing infrastructure provides:

1. **Pre-built Test Plugins**: Ready-to-use implementations for common testing scenarios
2. **Test Helper Utilities**: Tools for managing test plugins programmatically
3. **Pytest Fixtures**: Pre-configured fixtures for easy test setup
4. **Isolation**: Each test gets clean plugin instances and temporary directories
5. **Comprehensive Coverage**: Test discovery, loading, execution, dependencies, and error handling

Use these tools to write reliable integration tests for the plugin system and ensure plugins work correctly in realistic scenarios.
