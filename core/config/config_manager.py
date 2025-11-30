"""
Unified Configuration Manager

Manages application configuration with support for:
- YAML configuration files
- Environment variable overrides
- Schema validation
- Core and plugin config separation
- Hot reload capability

Author: RealEstatesAntiFraud Core Team
"""

import logging
import os
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file is not found."""

    pass


class CoreConfig(BaseModel):
    """Core application configuration schema."""

    app_name: str = Field(default="RealEstatesAntiFraud")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(
        default="development", pattern="^(development|staging|production)$"
    )
    debug: bool = Field(default=False)

    # API settings
    api_host: str = Field(default="0.0.0.0")  # nosec B104
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_workers: int = Field(default=4, ge=1)
    api_reload: bool = Field(default=False)

    # Database settings
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="realestates_antifraud")
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="")
    db_pool_size: int = Field(default=10, ge=1)
    db_max_overflow: int = Field(default=20, ge=0)

    # Redis cache settings
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0)
    redis_password: Optional[str] = Field(default=None)

    # Message queue settings
    mq_type: str = Field(default="rabbitmq", pattern="^(rabbitmq|kafka)$")
    mq_host: str = Field(default="localhost")
    mq_port: int = Field(default=5672, ge=1, le=65535)
    mq_user: str = Field(default="guest")
    mq_password: str = Field(default="guest")

    # Plugin settings
    plugins_dir: str = Field(default="plugins")
    plugins_autoload: bool = Field(default=True)
    plugins_hot_reload: bool = Field(default=False)

    # Logging settings
    log_level: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    log_format: str = Field(default="json", pattern="^(json|text)$")
    log_file: Optional[str] = Field(default=None)

    class Config:
        extra = "allow"  # Allow additional fields for extensibility


class PluginConfig(BaseModel):
    """Plugin-specific configuration schema."""

    plugin_id: str = Field(..., min_length=1)
    enabled: bool = Field(default=True)
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ConfigManager:
    """
    Manages application and plugin configuration.

    Features:
    - Load YAML configuration files
    - Environment variable overrides (CORE_* prefix for core, PLUGIN_* for plugins)
    - Schema validation using Pydantic
    - Separate core and plugin configs
    - Thread-safe operations
    - Hot reload support

    Environment variable naming convention:
    - Core: CORE_<SECTION>_<KEY> (e.g., CORE_DB_HOST)
    - Nested: Use double underscore (e.g., CORE_API__HOST)
    - Plugins: PLUGIN_<PLUGIN_ID>_<KEY>

    Thread-safety: All operations are thread-safe using RLock.
    """

    _instance = None
    _lock = RLock()

    def __new__(
        cls, config_dir: Optional[Union[str, Path]] = None, force_new: bool = False
    ):
        """
        Singleton pattern implementation.

        Args:
            config_dir: Directory containing config files
            force_new: Force creation of new instance (for testing)
        """
        if force_new:
            return super().__new__(cls)

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, config_dir: Optional[Union[str, Path]] = None, force_new: bool = False
    ):
        """
        Initialize ConfigManager.

        Args:
            config_dir: Directory containing config files. Defaults to ./config
            force_new: Force creation of new instance (for testing)
        """
        # Prevent re-initialization of singleton (unless force_new)
        if not force_new and hasattr(self, "_initialized_flag"):
            return

        self._config_dir = Path(config_dir) if config_dir else Path("config")
        self._core_config: Optional[CoreConfig] = None
        self._plugin_configs: Dict[str, PluginConfig] = {}
        self._raw_config: Dict[str, Any] = {}
        self._initialized = False
        self._initialized_flag = True

        logger.debug(f"ConfigManager initialized with config_dir: {self._config_dir}")

    def load(self, core_config_file: str = "core.yaml") -> None:
        """
        Load core configuration from YAML file with environment overrides.

        Args:
            core_config_file: Core configuration filename

        Raises:
            ConfigNotFoundError: If config file doesn't exist
            ConfigValidationError: If config validation fails
        """
        with self._lock:
            config_path = self._config_dir / core_config_file

            if not config_path.exists():
                raise ConfigNotFoundError(f"Core config file not found: {config_path}")

            logger.info(f"Loading core configuration from {config_path}")

            try:
                # Load YAML file
                with open(config_path, "r") as f:
                    raw_config = yaml.safe_load(f) or {}

                # Apply environment variable overrides
                config_with_env = self._apply_env_overrides(raw_config, "CORE")

                # Validate against schema
                self._core_config = CoreConfig(**config_with_env)
                self._raw_config = config_with_env
                self._initialized = True

                logger.info(
                    f"Core configuration loaded successfully "
                    f"(environment: {self._core_config.environment})"
                )

            except yaml.YAMLError as e:
                raise ConfigValidationError(f"Invalid YAML in {config_path}: {e}")
            except ValidationError as e:
                raise ConfigValidationError(f"Config validation failed: {e}")
            except Exception as e:
                raise ConfigError(f"Failed to load config: {e}")

    def load_plugin_config(
        self, plugin_id: str, config_file: Optional[str] = None
    ) -> PluginConfig:
        """
        Load plugin-specific configuration.

        Args:
            plugin_id: Plugin identifier
            config_file: Plugin config file path (optional)

        Returns:
            PluginConfig instance

        Raises:
            ConfigValidationError: If config validation fails
        """
        with self._lock:
            # Try to load from file if provided
            if config_file:
                config_path = self._config_dir / config_file
                if config_path.exists():
                    try:
                        with open(config_path, "r") as f:
                            raw_config = yaml.safe_load(f) or {}
                    except yaml.YAMLError as e:
                        raise ConfigValidationError(
                            f"Invalid YAML in {config_file}: {e}"
                        )
                else:
                    raw_config = {}
            else:
                raw_config = {}

            # Apply environment overrides for this plugin
            env_prefix = f"PLUGIN_{plugin_id.upper().replace('-', '_')}"
            config_with_env = self._apply_env_overrides(
                raw_config.get("config", {}), env_prefix
            )

            # Create plugin config
            try:
                plugin_config = PluginConfig(
                    plugin_id=plugin_id,
                    enabled=raw_config.get("enabled", True),
                    config=config_with_env,
                )

                self._plugin_configs[plugin_id] = plugin_config
                logger.debug(f"Loaded config for plugin: {plugin_id}")

                return plugin_config

            except ValidationError as e:
                raise ConfigValidationError(
                    f"Plugin config validation failed for {plugin_id}: {e}"
                )

    def get_core_config(self) -> CoreConfig:
        """
        Get core configuration.

        Returns:
            CoreConfig instance

        Raises:
            ConfigError: If config not loaded
        """
        if not self._initialized or self._core_config is None:
            raise ConfigError("Core configuration not loaded. Call load() first.")
        return self._core_config

    def get_plugin_config(self, plugin_id: str) -> Optional[PluginConfig]:
        """
        Get plugin configuration.

        Args:
            plugin_id: Plugin identifier

        Returns:
            PluginConfig or None if not loaded
        """
        return self._plugin_configs.get(plugin_id)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key with dot notation.

        Args:
            key: Configuration key (e.g., 'db_host' or 'api.port')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if not self._initialized:
            return default

        try:
            # Support dot notation for nested access
            keys = key.split(".")
            value = self._raw_config

            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default

            return value if value is not None else default

        except Exception:
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value dynamically (runtime only, not persisted).

        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        with self._lock:
            keys = key.split(".")
            current = self._raw_config

            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            current[keys[-1]] = value
            logger.debug(f"Config value set: {key} = {value}")

    def reload(self) -> None:
        """
        Reload configuration from files.

        Raises:
            ConfigError: If reload fails
        """
        logger.info("Reloading configuration")
        self.load()

        # Reload plugin configs
        plugin_ids = list(self._plugin_configs.keys())
        for plugin_id in plugin_ids:
            try:
                self.load_plugin_config(plugin_id)
            except Exception as e:
                logger.warning(f"Failed to reload config for {plugin_id}: {e}")

    def _apply_env_overrides(
        self, config: Dict[str, Any], prefix: str
    ) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Args:
            config: Base configuration dictionary
            prefix: Environment variable prefix (e.g., 'CORE' or 'PLUGIN_xxx')

        Returns:
            Configuration with environment overrides applied
        """
        result = config.copy()

        # Scan environment for matching variables
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(f"{prefix}_"):
                continue

            # Remove prefix and convert to lowercase
            config_key = env_key[len(prefix) + 1 :].lower()

            # Handle nested keys (double underscore)
            if "__" in config_key:
                keys = config_key.split("__")
                current = result

                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                current[keys[-1]] = self._cast_env_value(env_value)
            else:
                result[config_key] = self._cast_env_value(env_value)

        return result

    def _cast_env_value(self, value: str) -> Any:
        """
        Cast environment variable string to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Casted value (bool, int, float, or str)
        """
        # Boolean
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    def is_loaded(self) -> bool:
        """Check if configuration is loaded."""
        return self._initialized

    def get_config_dir(self) -> Path:
        """Get configuration directory path."""
        return self._config_dir

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConfigManager(config_dir={self._config_dir}, "
            f"loaded={self._initialized}, "
            f"plugins={len(self._plugin_configs)})"
        )


# Global singleton instance
config_manager = ConfigManager()
