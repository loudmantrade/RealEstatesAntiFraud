# Plugin Manifest Specification v1.0

**Document Version:** 1.0.0
**API Version:** 1.0
**Last Updated:** 2025-11-25

## Overview

This document defines the **Plugin Manifest Specification v1** for RealEstatesAntiFraud plugins. The manifest file (`plugin.yaml`) is the primary descriptor that enables the core system to discover, validate, load, and manage plugins.

## Design Principles

1. **Declarative**: Plugins declare their capabilities, not implementation details
2. **Versioned**: Clear API and manifest versioning for compatibility tracking
3. **Extensible**: Support for future fields without breaking existing plugins
4. **Validatable**: Machine-readable schema for automated validation
5. **Self-documenting**: Manifest provides all necessary metadata

## File Format

- **Filename**: `plugin.yaml` (mandatory, must be in plugin root directory)
- **Format**: YAML 1.2
- **Encoding**: UTF-8
- **Max Size**: 100 KB

## Schema Definition

### Required Fields

All plugin manifests MUST include these fields:

```yaml
# === REQUIRED FIELDS ===

# Unique identifier (kebab-case, prefix with plugin-{type}-)
id: string  # pattern: ^plugin-(source|processing|detection|search|display)-[a-z0-9-]+$

# Human-readable name
name: string  # max 100 chars

# Semantic version (semver 2.0.0)
version: string  # pattern: ^\d+\.\d+\.\d+(-[a-z0-9.-]+)?(\+[a-z0-9.-]+)?$

# Plugin type
type: enum  # source | processing | detection | search | display

# Manifest schema version
api_version: string  # "1.0" for this spec

# Brief description
description: string  # max 500 chars, supports multiline
```

### Optional Fields

#### 1. Author Information

```yaml
author:
  name: string          # Author/organization name
  email: string         # Contact email (RFC 5322)
  url: string           # Website or repository URL
```

#### 2. Licensing

```yaml
license: string         # SPDX license identifier or "Proprietary"
repository: string      # Git repository URL
homepage: string        # Documentation homepage
```

#### 3. Dependencies

```yaml
dependencies:
  # Minimum core system version
  core_version: string  # semver constraint, e.g., ">=1.0.0,<2.0.0"

  # Python version requirement
  python_version: string  # e.g., ">=3.10,<4.0"

  # Other plugin dependencies
  plugins:
    plugin-id: string   # semver constraint for each plugin

  # System dependencies (informational)
  system:
    - name: string      # e.g., "redis", "postgresql"
      version: string   # optional version requirement
```

#### 4. Configuration Schema

```yaml
config:
  # Path to JSON Schema file for config validation
  schema: string        # relative path, e.g., "config.schema.json"

  # Required configuration keys
  required_keys:
    - string            # key names that must be provided

  # Default configuration (merged with user config)
  defaults:
    key: value          # any valid YAML structure
```

#### 5. Capabilities

```yaml
capabilities:
  # List of feature flags (plugin-type specific)
  - string              # e.g., "incremental_scraping", "real_time", "batch"
```

**Capabilities by Plugin Type:**

- **Source**: `incremental_scraping`, `real_time_updates`, `batch_processing`, `pagination`, `authentication_required`
- **Processing**: `async_processing`, `batch_operations`, `parallel_safe`, `stateful`
- **Detection**: `ml_model`, `rule_based`, `real_time`, `explainable`
- **Search**: `full_text`, `faceted_search`, `geo_search`, `fuzzy_matching`, `autocomplete`
- **Display**: `templating`, `custom_css`, `interactive`, `export_formats`

#### 6. Resource Requirements

```yaml
resources:
  memory_mb: integer    # Expected memory usage (MB)
  cpu_cores: float      # CPU cores (e.g., 0.5, 1, 2)
  disk_mb: integer      # Persistent disk space (MB)
  network: enum         # none | low | medium | high
```

#### 7. Lifecycle Hooks

```yaml
hooks:
  on_install: string    # Script path to run after plugin installation
  on_enable: string     # Script path to run when plugin is enabled
  on_disable: string    # Script path to run when plugin is disabled
  on_uninstall: string  # Script path to run before plugin removal
  on_configure: string  # Script path to run after configuration changes
```

**Hook Script Requirements:**
- Must be executable
- Exit code 0 = success, non-zero = failure
- Timeout: 60 seconds (configurable in core)
- Environment variables provided: `PLUGIN_ID`, `PLUGIN_DIR`, `CORE_VERSION`, `CONFIG_PATH`

#### 8. Metrics

```yaml
metrics:
  - name: string        # Metric name (snake_case)
    type: enum          # counter | gauge | histogram | summary
    description: string # What the metric measures
    unit: string        # Unit of measurement (optional)
    labels:             # Metric labels (optional)
      - string
```

#### 9. Health Check

```yaml
health:
  endpoint: string      # HTTP endpoint path for health check
  interval: integer     # Check interval in seconds (default: 60)
  timeout: integer      # Timeout in seconds (default: 5)
  retries: integer      # Retry count (default: 3)
```

#### 10. Entrypoint

```yaml
entrypoint:
  module: string        # Python module path, e.g., "plugin.main"
  class: string         # Class name implementing plugin interface
```

#### 11. Tags

```yaml
tags:
  - string              # Searchable tags for plugin discovery
```

#### 12. Compatibility

```yaml
compatibility:
  platforms:
    - string            # linux | darwin | windows
  architectures:
    - string            # x86_64 | arm64 | aarch64
  exclude_versions:
    core: [string]      # Core versions to exclude (e.g., ["1.0.0", "1.0.1"])
```

#### 13. Metadata

```yaml
metadata:
  icon: string          # Path to plugin icon (PNG, 128x128)
  screenshots:
    - string            # Paths to screenshot images
  keywords:
    - string            # Search keywords
  category: string      # Plugin category for marketplace
  mature: boolean       # Production-ready flag (default: false)
```

## Complete Example: Source Plugin

```yaml
# === REQUIRED ===
id: plugin-source-avito
name: Avito Real Estate Scraper
version: 1.2.3
type: source
api_version: "1.0"
description: |
  Scrapes real estate listings from Avito.ru with anti-detection
  capabilities. Supports incremental updates and real-time monitoring.

# === OPTIONAL ===
author:
  name: RealEstates Team
  email: plugins@realestates.dev
  url: https://github.com/realestates/plugin-source-avito

license: MIT
repository: https://github.com/realestates/plugin-source-avito
homepage: https://docs.realestates.dev/plugins/source/avito

dependencies:
  core_version: ">=1.0.0,<2.0.0"
  python_version: ">=3.10,<4.0"
  plugins:
    plugin-processing-normalizer: ">=1.0.0"
  system:
    - name: redis
      version: ">=6.0"

config:
  schema: "config.schema.json"
  required_keys:
    - regions
    - update_interval
  defaults:
    regions: ["moscow", "spb"]
    update_interval: 3600
    max_pages: 50
    use_proxy: true

capabilities:
  - incremental_scraping
  - real_time_updates
  - batch_processing
  - authentication_required

resources:
  memory_mb: 512
  cpu_cores: 1
  disk_mb: 100
  network: medium

hooks:
  on_install: scripts/setup.sh
  on_enable: scripts/start_worker.sh
  on_disable: scripts/stop_worker.sh

metrics:
  - name: listings_scraped_total
    type: counter
    description: Total number of listings successfully scraped
    labels: [region, property_type]
  - name: scraping_duration_seconds
    type: histogram
    description: Time taken to scrape a page
    unit: seconds
  - name: active_scraping_tasks
    type: gauge
    description: Number of concurrent scraping tasks

health:
  endpoint: /health
  interval: 30
  timeout: 5
  retries: 2

entrypoint:
  module: avito_scraper.plugin
  class: AvitoSourcePlugin

tags:
  - avito
  - russia
  - real-estate
  - scraper

compatibility:
  platforms: [linux, darwin]
  architectures: [x86_64, arm64]

metadata:
  icon: assets/icon.png
  screenshots:
    - docs/screenshot1.png
    - docs/screenshot2.png
  keywords:
    - avito
    - scraper
    - russia
    - real estate
  category: sources
  mature: true
```

## Complete Example: Processing Plugin

```yaml
id: plugin-processing-geocoder
name: Location Geocoding Plugin
version: 2.0.1
type: processing
api_version: "1.0"
description: |
  Enriches listings with precise coordinates using multiple
  geocoding services (Google, Yandex, OSM) with fallback.

author:
  name: GeoTeam
  email: geo@realestates.dev

license: Apache-2.0
repository: https://github.com/realestates/plugin-processing-geocoder

dependencies:
  core_version: ">=1.0.0"
  python_version: ">=3.11"

config:
  schema: "config.schema.json"
  required_keys:
    - providers
  defaults:
    providers:
      - name: yandex
        api_key: "${YANDEX_API_KEY}"
        priority: 1
      - name: google
        api_key: "${GOOGLE_API_KEY}"
        priority: 2
      - name: osm
        priority: 3
    cache_ttl: 86400
    retry_attempts: 3

capabilities:
  - async_processing
  - parallel_safe
  - caching

resources:
  memory_mb: 256
  cpu_cores: 0.5
  disk_mb: 50
  network: high

metrics:
  - name: geocoding_requests_total
    type: counter
    labels: [provider, status]
  - name: geocoding_cache_hits
    type: counter
  - name: geocoding_latency_seconds
    type: histogram
    labels: [provider]

entrypoint:
  module: geocoder.plugin
  class: GeocoderPlugin

tags:
  - geocoding
  - location
  - coordinates
```

## Complete Example: Detection Plugin

```yaml
id: plugin-detection-price-anomaly
name: Price Anomaly Detector
version: 1.5.0
type: detection
api_version: "1.0"
description: |
  ML-based price anomaly detection using Isolation Forest
  and Z-score analysis. Identifies suspiciously low/high prices.

author:
  name: ML Team
  email: ml@realestates.dev

license: MIT
repository: https://github.com/realestates/plugin-detection-price

dependencies:
  core_version: ">=1.0.0"
  python_version: ">=3.10"

config:
  schema: "config.schema.json"
  required_keys:
    - model_path
    - threshold
  defaults:
    model_path: models/isolation_forest.pkl
    threshold: 0.8
    update_frequency: daily
    features:
      - price_per_sqm
      - location_score
      - property_age

capabilities:
  - ml_model
  - explainable
  - real_time

resources:
  memory_mb: 1024
  cpu_cores: 2
  disk_mb: 500
  network: low

metrics:
  - name: detections_total
    type: counter
    labels: [anomaly_type, confidence_level]
  - name: model_inference_duration
    type: histogram
  - name: false_positive_rate
    type: gauge

hooks:
  on_install: scripts/download_model.sh
  on_configure: scripts/retrain_model.sh

entrypoint:
  module: price_detector.plugin
  class: PriceAnomalyDetector

tags:
  - ml
  - anomaly-detection
  - price
  - fraud
```

## Complete Example: Search Plugin

```yaml
id: plugin-search-elasticsearch
name: Elasticsearch Search Plugin
version: 3.1.0
type: search
api_version: "1.0"
description: |
  Full-text search using Elasticsearch with faceted filters,
  geo-search, and fuzzy matching support.

author:
  name: Search Team
  email: search@realestates.dev

license: Apache-2.0
repository: https://github.com/realestates/plugin-search-elasticsearch

dependencies:
  core_version: ">=1.0.0"
  python_version: ">=3.10"
  system:
    - name: elasticsearch
      version: ">=8.0,<9.0"

config:
  schema: "config.schema.json"
  required_keys:
    - elasticsearch_url
    - index_name
  defaults:
    elasticsearch_url: "http://localhost:9200"
    index_name: listings
    refresh_interval: "1s"
    number_of_replicas: 1

capabilities:
  - full_text
  - faceted_search
  - geo_search
  - fuzzy_matching
  - autocomplete

resources:
  memory_mb: 2048
  cpu_cores: 2
  disk_mb: 10000
  network: high

health:
  endpoint: /_health
  interval: 60
  timeout: 10

metrics:
  - name: search_requests_total
    type: counter
    labels: [query_type]
  - name: search_latency_seconds
    type: histogram
  - name: index_size_bytes
    type: gauge

entrypoint:
  module: elasticsearch_plugin.plugin
  class: ElasticsearchSearchPlugin

tags:
  - elasticsearch
  - search
  - full-text
```

## Complete Example: Display Plugin

```yaml
id: plugin-display-card
name: Card View Display Plugin
version: 1.0.0
type: display
api_version: "1.0"
description: |
  Renders listings in compact card format with customizable
  fields and responsive design.

author:
  name: UI Team
  email: ui@realestates.dev

license: MIT

dependencies:
  core_version: ">=1.0.0"
  python_version: ">=3.10"

config:
  defaults:
    fields: [image, title, price, location]
    card_width: 320
    show_fraud_badge: true

capabilities:
  - templating
  - custom_css
  - responsive

resources:
  memory_mb: 64
  cpu_cores: 0.1
  disk_mb: 10

entrypoint:
  module: card_view.plugin
  class: CardDisplayPlugin

tags:
  - display
  - ui
  - card
```

## Validation Rules

### 1. ID Validation
- Must match pattern: `^plugin-(source|processing|detection|search|display)-[a-z0-9-]+$`
- Must be unique across all installed plugins
- Cannot be changed after initial registration

### 2. Version Validation
- Must follow Semantic Versioning 2.0.0
- Format: `MAJOR.MINOR.PATCH[-prerelease][+build]`
- Examples: `1.0.0`, `2.1.3-beta.1`, `1.0.0+20231125`

### 3. Type Validation
- Must be one of: `source`, `processing`, `detection`, `search`, `display`
- Determines which interface the plugin must implement

### 4. API Version
- Current version: `"1.0"`
- Core system will validate compatibility

### 5. Dependency Constraints
- Use npm-style semver ranges:
  - `1.0.0` - exact version
  - `>=1.0.0` - minimum version
  - `>=1.0.0,<2.0.0` - range
  - `^1.0.0` - compatible (allows 1.x.x)
  - `~1.0.0` - patch-level (allows 1.0.x)

### 6. Resource Limits
- `memory_mb`: 1 - 16384
- `cpu_cores`: 0.1 - 32.0
- `disk_mb`: 1 - 102400

### 7. File Size
- `plugin.yaml`: max 100 KB
- Icon (if provided): max 1 MB, PNG format, recommended 128x128px

## Error Handling

The core system will reject plugin registration if:

1. **Syntax Error**: Invalid YAML syntax
2. **Schema Violation**: Missing required fields or invalid types
3. **ID Conflict**: Plugin ID already registered
4. **Version Invalid**: Non-semver version string
5. **Dependency Unmet**: Required core version not satisfied
6. **Entrypoint Missing**: Specified Python module/class not found
7. **Interface Mismatch**: Plugin class doesn't implement required interface

Error messages will include:
- Error code (e.g., `MANIFEST_INVALID`)
- Detailed description
- Line number (for YAML parsing errors)
- Suggestion for fix

## Versioning Strategy

### Manifest Versions

- **v1.0** (current): Initial specification
- Future versions will be backward compatible within major version
- Breaking changes will increment major version (v2.0, v3.0)

### Plugin Versioning Best Practices

1. **MAJOR**: Incompatible API changes, breaking changes
2. **MINOR**: New features, backward compatible
3. **PATCH**: Bug fixes, backward compatible

## Migration Path

When manifest spec is updated:

1. **Backward Compatibility**: v1.x plugins will work with v1.y core (y > x)
2. **Deprecation Warnings**: Old fields will be marked deprecated but still work
3. **Migration Guide**: Documentation provided for upgrading manifests
4. **Validation Warnings**: Core will warn about deprecated fields

## JSON Schema Reference

The formal JSON Schema for validation is available at:
- **File**: `schemas/plugin-manifest-v1.schema.json`
- **URL**: `https://schemas.realestates.dev/plugin-manifest/v1.0/schema.json`

## Security Considerations

1. **Hooks**: Scripts run with plugin user permissions (sandboxed)
2. **Config**: Secrets should use environment variable substitution (`${VAR}`)
3. **Dependencies**: Core validates checksums for critical dependencies
4. **Code Signing**: Future versions will support signed manifests

## Best Practices

1. ✅ **Keep manifests minimal**: Only include necessary fields
2. ✅ **Use semantic versioning**: Follow semver strictly
3. ✅ **Document capabilities**: List all features your plugin supports
4. ✅ **Specify resources accurately**: Help core optimize resource allocation
5. ✅ **Include health checks**: Enable monitoring and auto-recovery
6. ✅ **Tag appropriately**: Improve discoverability
7. ✅ **Test validation**: Use `make plugin-validate` before publishing
8. ❌ **Avoid hardcoded secrets**: Use environment variables
9. ❌ **Don't change ID**: ID is immutable identifier
10. ❌ **Don't skip required fields**: All required fields must be present

## Tools & Utilities

### Validation Tool

```bash
# Validate plugin manifest
make plugin-validate PLUGIN=path/to/plugin

# Or use CLI directly
core plugin validate path/to/plugin/plugin.yaml
```

### Manifest Generator

```bash
# Interactive manifest creator
core plugin init --type source --name my-plugin
```

### Schema Validation in Python

```python
from core.utils.plugin_validator import validate_manifest

with open('plugin.yaml') as f:
    manifest = yaml.safe_load(f)

errors = validate_manifest(manifest, api_version='1.0')
if errors:
    for error in errors:
        print(f"Error: {error}")
```

## References

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Plugin Development Guide**: [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md)
- **Core API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **JSON Schema Spec**: [schemas/plugin-manifest-v1.schema.json](../schemas/plugin-manifest-v1.schema.json)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-25 | Initial specification release |

---

**Maintained by**: RealEstatesAntiFraud Core Team
**Questions**: Open an issue at https://github.com/loudmantrade/RealEstatesAntiFroud/issues
