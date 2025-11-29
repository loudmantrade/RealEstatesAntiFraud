"""
Integration tests for ConfigManager.

Tests real file I/O, environment variables, configuration loading,
hot reload, and multi-environment scenarios.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest
import yaml

from core.config import ConfigManager, ConfigNotFoundError, ConfigValidationError


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory with test files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def core_config_yaml(temp_config_dir):
    """Create a basic core config YAML file."""
    config = {
        "app_name": "TestApp",
        "environment": "development",
        "debug": True,
        "api_port": 9000,
        "db_host": "testdb.local",
        "db_port": 5432,
        "db_name": "test_db",
        "redis_host": "redis.local",
    }
    config_path = temp_config_dir / "core.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def plugin_config_yaml(temp_config_dir):
    """Create a plugin config YAML file."""
    config = {"plugin_id": "test-plugin", "enabled": True, "config": {"timeout": 30}}
    config_path = temp_config_dir / "plugin-test.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def clean_env():
    """Clean environment variables before and after tests."""
    # Save original env
    original_env = os.environ.copy()

    # Clear all CORE_* and PLUGIN_* vars
    for key in list(os.environ.keys()):
        if key.startswith("CORE_") or key.startswith("PLUGIN_"):
            del os.environ[key]

    yield

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


class TestConfigurationLoading:
    """Test configuration loading from files."""

    def test_load_core_config_from_yaml(self, temp_config_dir, core_config_yaml):
        """Test loading core configuration from YAML file."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        core_config = manager.get_core_config()
        assert core_config.app_name == "TestApp"
        assert manager.get("app_name") == "TestApp"
        assert manager.get("environment") == "development"
        assert manager.get("debug") is True
        assert manager.get("api_port") == 9000
        assert manager.get("db_host") == "testdb.local"

    def test_load_config_file_not_found(self, temp_config_dir):
        """Test loading config when file doesn't exist."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)

        with pytest.raises(ConfigNotFoundError):
            manager.load("nonexistent.yaml")

    def test_load_invalid_yaml_syntax(self, temp_config_dir):
        """Test loading config with invalid YAML syntax."""
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: syntax: [")

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)

        with pytest.raises(ConfigValidationError):
            manager.load()

    def test_load_config_with_validation_error(self, temp_config_dir):
        """Test loading config with schema validation errors."""
        config = {"app_name": "TestApp", "api_port": 99999}  # Invalid port
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)

        with pytest.raises(ConfigValidationError):
            manager.load()

    def test_load_config_multiple_times_is_idempotent(
        self, temp_config_dir, core_config_yaml
    ):
        """Test loading config multiple times doesn't cause issues."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()
        first_value = manager.get("app_name")

        manager.load()  # Load again
        second_value = manager.get("app_name")

        assert first_value == second_value == "TestApp"


class TestEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_env_override_single_value(
        self, temp_config_dir, core_config_yaml, clean_env
    ):
        """Test environment variable overrides single config value."""
        os.environ["CORE_API_PORT"] = "8888"

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("api_port") == 8888

    def test_env_override_multiple_values(
        self, temp_config_dir, core_config_yaml, clean_env
    ):
        """Test multiple environment variable overrides."""
        os.environ["CORE_DB_HOST"] = "prod-db.example.com"
        os.environ["CORE_DB_PORT"] = "3306"
        os.environ["CORE_ENVIRONMENT"] = "production"

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("db_host") == "prod-db.example.com"
        assert manager.get("db_port") == 3306
        assert manager.get("environment") == "production"

    def test_env_override_boolean_values(
        self, temp_config_dir, core_config_yaml, clean_env
    ):
        """Test environment variable override for boolean values."""
        os.environ["CORE_DEBUG"] = "false"
        os.environ["CORE_API_RELOAD"] = "true"

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("debug") is False
        assert manager.get("api_reload") is True

    def test_env_override_takes_precedence_over_file(
        self, temp_config_dir, core_config_yaml, clean_env
    ):
        """Test that environment variables take precedence over file values."""
        # File has api_port: 9000
        os.environ["CORE_API_PORT"] = "7777"

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("api_port") == 7777  # ENV wins

    def test_env_with_defaults_when_no_file(self, temp_config_dir, clean_env):
        """Test environment variables work with defaults when no file exists."""
        os.environ["CORE_APP_NAME"] = "EnvOnlyApp"
        os.environ["CORE_API_PORT"] = "5555"

        # Create minimal valid config
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump({}, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("app_name") == "EnvOnlyApp"
        assert manager.get("api_port") == 5555


class TestPluginConfiguration:
    """Test plugin-specific configuration."""

    def test_load_plugin_config_from_file(
        self, temp_config_dir, core_config_yaml, plugin_config_yaml
    ):
        """Test loading plugin configuration from file."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        plugin_config = manager.load_plugin_config(
            "test-plugin", config_file="plugin-test.yaml"
        )

        assert plugin_config.plugin_id == "test-plugin"
        assert plugin_config.enabled is True
        assert plugin_config.config["timeout"] == 30

    def test_load_plugin_config_without_file(self, temp_config_dir, core_config_yaml):
        """Test loading plugin config when file doesn't exist."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        plugin_config = manager.load_plugin_config("new-plugin")

        assert plugin_config.plugin_id == "new-plugin"
        assert plugin_config.enabled is True
        assert plugin_config.config == {}

    def test_plugin_env_override(
        self, temp_config_dir, core_config_yaml, plugin_config_yaml, clean_env
    ):
        """Test plugin configuration override via environment."""
        os.environ["PLUGIN_TEST_PLUGIN_ENABLED"] = "false"
        os.environ["PLUGIN_TEST_PLUGIN_TIMEOUT"] = "60"

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        plugin_config = manager.load_plugin_config(
            "test-plugin", config_file="plugin-test.yaml"
        )

        # ENV vars go into config dict and are converted to proper types
        assert plugin_config.config.get("enabled") is False
        assert plugin_config.config.get("timeout") == 60

    def test_multiple_plugin_configs(self, temp_config_dir, core_config_yaml):
        """Test loading multiple plugin configurations."""
        # Create multiple plugin configs
        for i in range(3):
            config = {
                "plugin_id": f"plugin-{i}",
                "enabled": True,
                "config": {"value": i * 10},
            }
            config_path = temp_config_dir / f"plugin-{i}.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        for i in range(3):
            plugin_config = manager.load_plugin_config(
                f"plugin-{i}", config_file=f"plugin-{i}.yaml"
            )
            assert plugin_config.plugin_id == f"plugin-{i}"
            assert plugin_config.config["value"] == i * 10


class TestMultiEnvironment:
    """Test multi-environment configurations."""

    def test_development_environment(self, temp_config_dir):
        """Test development environment configuration."""
        config = {
            "environment": "development",
            "debug": True,
            "api_reload": True,
            "db_host": "localhost",
        }
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("environment") == "development"
        assert manager.get("debug") is True
        assert manager.get("api_reload") is True

    def test_production_environment(self, temp_config_dir):
        """Test production environment configuration."""
        config = {
            "environment": "production",
            "debug": False,
            "api_reload": False,
            "db_host": "prod-db.example.com",
        }
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("environment") == "production"
        assert manager.get("debug") is False
        assert manager.get("api_reload") is False

    def test_staging_environment(self, temp_config_dir):
        """Test staging environment configuration."""
        config = {"environment": "staging", "debug": True, "db_host": "staging-db"}
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("environment") == "staging"

    def test_environment_specific_overrides(self, temp_config_dir, clean_env):
        """Test environment-specific configuration overrides."""
        # Base config
        config = {"environment": "development", "api_port": 8000}
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        # Override for production
        os.environ["CORE_ENVIRONMENT"] = "production"
        os.environ["CORE_DEBUG"] = "false"
        os.environ["CORE_API_PORT"] = "80"

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        assert manager.get("environment") == "production"
        assert manager.get("debug") is False
        assert manager.get("api_port") == 80


class TestConfigurationGetters:
    """Test configuration getter methods."""

    def test_get_existing_value(self, temp_config_dir, core_config_yaml):
        """Test getting existing configuration value."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        value = manager.get("app_name")
        assert value == "TestApp"

    def test_get_with_default(self, temp_config_dir, core_config_yaml):
        """Test getting value with default fallback."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        value = manager.get("nonexistent_key", default="default_value")
        assert value == "default_value"

    def test_get_nested_value(self, temp_config_dir):
        """Test getting nested configuration value."""
        config = {"database": {"connection": {"host": "nested.db"}}}
        config_path = temp_config_dir / "core.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        # Test dot notation access
        host = manager.get("database.connection.host")
        assert host == "nested.db"

    def test_get_all_config(self, temp_config_dir, core_config_yaml):
        """Test getting all configuration as dict."""
        manager = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager.load()

        core_config = manager.get_core_config()
        assert core_config.app_name == "TestApp"
        assert core_config.api_port == 9000


class TestThreadSafety:
    """Test thread-safe operations."""

    def test_singleton_pattern(self, temp_config_dir):
        """Test ConfigManager follows singleton pattern."""
        manager1 = ConfigManager(config_dir=temp_config_dir)
        manager2 = ConfigManager(config_dir=temp_config_dir)

        assert manager1 is manager2

    def test_force_new_creates_separate_instance(self, temp_config_dir):
        """Test force_new parameter creates separate instance."""
        manager1 = ConfigManager(config_dir=temp_config_dir, force_new=True)
        manager2 = ConfigManager(config_dir=temp_config_dir, force_new=True)

        assert manager1 is not manager2
