# Configuration Directory

This directory contains YAML configuration files for the application.

## Files

- `core.yaml` - Main configuration file for development
- `core.production.yaml` - Production environment overrides
- `plugin-example.yaml` - Example plugin configuration template

## Environment Variable Overrides

Configuration values can be overridden using environment variables:

### Core Configuration
Format: `CORE_<KEY>=value`

Examples:
```bash
export CORE_DB_HOST=localhost
export CORE_DB_PASSWORD=secret123
export CORE_API_PORT=8080
export CORE_LOG_LEVEL=DEBUG
```

### Nested Configuration
Use double underscore for nested keys: `CORE_<SECTION>__<KEY>=value`

Examples:
```bash
export CORE_DB__HOST=localhost
export CORE_API__PORT=8080
```

### Plugin Configuration
Format: `PLUGIN_<PLUGIN_ID>_<KEY>=value`

Examples:
```bash
export PLUGIN_CIAN_SCRAPER_API_KEY=abc123
export PLUGIN_CIAN_SCRAPER_RATE_LIMIT=50
```

## Loading Configuration

```python
from core.config import ConfigManager

# Initialize and load
config = ConfigManager()
config.load("core.yaml")

# Access values
core_config = config.get_core_config()
print(core_config.db_host)

# Get specific value
db_host = config.get("db_host")

# Load plugin config
plugin_config = config.load_plugin_config("cian-scraper", "plugin-cian.yaml")
```

## Security Notes

**Never commit sensitive data to this directory!**

- Use environment variables for passwords, API keys, and tokens
- Add sensitive config files to `.gitignore`
- Use a secrets management system in production (e.g., Vault, AWS Secrets Manager)
