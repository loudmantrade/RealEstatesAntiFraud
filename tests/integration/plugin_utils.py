"""Plugin testing utility classes for integration tests."""

import shutil
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class PluginTestHelper:
    """Helper class for creating and managing test plugins in integration tests.
    
    This utility provides methods to:
    - Create temporary plugin directories
    - Copy plugin fixtures to test locations
    - Create plugin manifests programmatically
    - Clean up test plugins after tests
    
    Example:
        helper = PluginTestHelper(tmp_path)
        plugin_dir = helper.copy_plugin_fixture("test_processing_plugin")
        # ... run tests ...
        helper.cleanup()
    """

    def __init__(self, base_dir: Path):
        """Initialize the helper with a base directory.
        
        Args:
            base_dir: Base directory for test plugins (typically pytest tmp_path)
        """
        self.base_dir = Path(base_dir)
        self.created_dirs: List[Path] = []
        
    def get_fixture_path(self, plugin_name: str) -> Path:
        """Get the path to a plugin fixture.
        
        Args:
            plugin_name: Name of the plugin fixture
            
        Returns:
            Path to the plugin fixture directory
        """
        # Assume fixtures are in tests/fixtures/plugins/
        fixture_base = Path(__file__).parent.parent / "fixtures" / "plugins"
        return fixture_base / plugin_name
    
    def copy_plugin_fixture(self, plugin_name: str, dest_name: Optional[str] = None) -> Path:
        """Copy a plugin fixture to the test directory.
        
        Args:
            plugin_name: Name of the plugin fixture to copy
            dest_name: Optional destination name (defaults to plugin_name)
            
        Returns:
            Path to the copied plugin directory
            
        Raises:
            FileNotFoundError: If the plugin fixture doesn't exist
        """
        source = self.get_fixture_path(plugin_name)
        if not source.exists():
            raise FileNotFoundError(f"Plugin fixture not found: {source}")
        
        dest_name = dest_name or plugin_name
        dest = self.base_dir / dest_name
        
        shutil.copytree(source, dest)
        self.created_dirs.append(dest)
        
        return dest
    
    def create_plugin_dir(
        self,
        plugin_id: str,
        plugin_name: str,
        plugin_type: str,
        entrypoint: str,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Create a plugin directory with a manifest file.
        
        Args:
            plugin_id: Plugin ID
            plugin_name: Human-readable plugin name
            plugin_type: Plugin type (source, processing, detection, etc.)
            entrypoint: Plugin entrypoint (module.ClassName)
            version: Plugin version (default: 1.0.0)
            capabilities: List of plugin capabilities
            dependencies: List of plugin dependencies (plugin IDs)
            configuration: Configuration schema dictionary
            
        Returns:
            Path to the created plugin directory
        """
        plugin_dir = self.base_dir / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)
        self.created_dirs.append(plugin_dir)
        
        manifest = {
            "id": plugin_id,
            "name": plugin_name,
            "version": version,
            "type": plugin_type,
            "entrypoint": entrypoint,
            "description": f"Test plugin: {plugin_name}",
            "author": "Test Suite",
            "license": "MIT",
        }
        
        if capabilities:
            manifest["capabilities"] = capabilities
        
        if dependencies:
            manifest["dependencies"] = dependencies
        
        if configuration:
            manifest["configuration"] = configuration
        
        manifest_path = plugin_dir / "plugin.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        
        return plugin_dir
    
    def create_plugin_file(
        self,
        plugin_dir: Path,
        filename: str,
        content: str,
    ) -> Path:
        """Create a Python file in the plugin directory.
        
        Args:
            plugin_dir: Plugin directory path
            filename: Name of the file to create
            content: Python code content
            
        Returns:
            Path to the created file
        """
        file_path = plugin_dir / filename
        with open(file_path, "w") as f:
            f.write(content)
        return file_path
    
    def list_plugins(self) -> List[Path]:
        """List all plugin directories in the base directory.
        
        Returns:
            List of paths to plugin directories (containing plugin.yaml)
        """
        plugins = []
        if self.base_dir.exists():
            for item in self.base_dir.iterdir():
                if item.is_dir() and (item / "plugin.yaml").exists():
                    plugins.append(item)
        return plugins
    
    def read_manifest(self, plugin_dir: Path) -> Dict[str, Any]:
        """Read a plugin manifest file.
        
        Args:
            plugin_dir: Path to the plugin directory
            
        Returns:
            Parsed manifest dictionary
            
        Raises:
            FileNotFoundError: If plugin.yaml doesn't exist
        """
        manifest_path = plugin_dir / "plugin.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        with open(manifest_path) as f:
            return yaml.safe_load(f)
    
    def cleanup(self) -> None:
        """Remove all created plugin directories.
        
        This should be called in test teardown to clean up temporary plugins.
        """
        for plugin_dir in self.created_dirs:
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
        self.created_dirs.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup()
