"""
Unit tests for plugin manifest validation.
"""
import json
import pytest
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError


@pytest.fixture
def schema():
    """Load JSON Schema."""
    schema_path = Path(__file__).parent.parent.parent / "schemas" / "plugin-manifest-v1.schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def valid_minimal_manifest():
    """Minimal valid plugin manifest."""
    return {
        "id": "plugin-source-test",
        "name": "Test Plugin",
        "version": "1.0.0",
        "type": "source",
        "api_version": "1.0",
        "description": "Test plugin"
    }


class TestRequiredFields:
    """Test required field validation."""
    
    def test_valid_minimal_manifest(self, schema, valid_minimal_manifest):
        """Minimal valid manifest should pass validation."""
        validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_missing_id(self, schema, valid_minimal_manifest):
        """Missing id should fail validation."""
        del valid_minimal_manifest["id"]
        with pytest.raises(ValidationError, match="'id' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_missing_name(self, schema, valid_minimal_manifest):
        """Missing name should fail validation."""
        del valid_minimal_manifest["name"]
        with pytest.raises(ValidationError, match="'name' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_missing_version(self, schema, valid_minimal_manifest):
        """Missing version should fail validation."""
        del valid_minimal_manifest["version"]
        with pytest.raises(ValidationError, match="'version' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_missing_type(self, schema, valid_minimal_manifest):
        """Missing type should fail validation."""
        del valid_minimal_manifest["type"]
        with pytest.raises(ValidationError, match="'type' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_missing_api_version(self, schema, valid_minimal_manifest):
        """Missing api_version should fail validation."""
        del valid_minimal_manifest["api_version"]
        with pytest.raises(ValidationError, match="'api_version' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_missing_description(self, schema, valid_minimal_manifest):
        """Missing description should fail validation."""
        del valid_minimal_manifest["description"]
        with pytest.raises(ValidationError, match="'description' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)


class TestIDValidation:
    """Test ID field validation."""
    
    @pytest.mark.parametrize("plugin_id", [
        "plugin-source-avito",
        "plugin-processing-geocoder",
        "plugin-detection-fraud-detector",
        "plugin-search-elasticsearch",
        "plugin-display-card-view",
        "plugin-source-test-123",
        "plugin-source-a-b-c",
    ])
    def test_valid_id_patterns(self, schema, valid_minimal_manifest, plugin_id):
        """Valid ID patterns should pass."""
        valid_minimal_manifest["id"] = plugin_id
        validate(instance=valid_minimal_manifest, schema=schema)
    
    @pytest.mark.parametrize("plugin_id", [
        "invalid-id",  # Missing plugin- prefix
        "plugin-invalid-type-test",  # Invalid type
        "plugin-source-Test",  # Uppercase letters
        "plugin-source-test_with_underscore",  # Underscores not allowed
        "plugin-source-",  # Empty name
        "source-plugin-test",  # Wrong order
    ])
    def test_invalid_id_patterns(self, schema, valid_minimal_manifest, plugin_id):
        """Invalid ID patterns should fail."""
        valid_minimal_manifest["id"] = plugin_id
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)


class TestVersionValidation:
    """Test version field validation (semver)."""
    
    @pytest.mark.parametrize("version", [
        "1.0.0",
        "0.1.0",
        "10.20.30",
        "1.0.0-alpha",
        "1.0.0-beta.1",
        "1.0.0-rc.1",
        "1.0.0+20231125",
        "1.0.0-beta.1+build.123",
    ])
    def test_valid_semver_versions(self, schema, valid_minimal_manifest, version):
        """Valid semver versions should pass."""
        valid_minimal_manifest["version"] = version
        validate(instance=valid_minimal_manifest, schema=schema)
    
    @pytest.mark.parametrize("version", [
        "1.0",  # Missing patch
        "1",  # Missing minor and patch
        "v1.0.0",  # v prefix not allowed
        "1.0.0.0",  # Too many parts
        "1.0.a",  # Invalid patch
    ])
    def test_invalid_semver_versions(self, schema, valid_minimal_manifest, version):
        """Invalid semver versions should fail."""
        valid_minimal_manifest["version"] = version
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)


class TestTypeValidation:
    """Test type field validation."""
    
    @pytest.mark.parametrize("plugin_type", [
        "source",
        "processing",
        "detection",
        "search",
        "display",
    ])
    def test_valid_types(self, schema, valid_minimal_manifest, plugin_type):
        """Valid plugin types should pass."""
        # Update ID to match type
        valid_minimal_manifest["id"] = f"plugin-{plugin_type}-test"
        valid_minimal_manifest["type"] = plugin_type
        validate(instance=valid_minimal_manifest, schema=schema)
    
    @pytest.mark.parametrize("plugin_type", [
        "Source",  # Wrong case
        "PROCESSING",  # Wrong case
        "invalid",  # Unknown type
        "api",  # Not a plugin type
    ])
    def test_invalid_types(self, schema, valid_minimal_manifest, plugin_type):
        """Invalid plugin types should fail."""
        valid_minimal_manifest["type"] = plugin_type
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)


class TestAPIVersionValidation:
    """Test api_version field validation."""
    
    def test_valid_api_version(self, schema, valid_minimal_manifest):
        """Current API version 1.0 should pass."""
        valid_minimal_manifest["api_version"] = "1.0"
        validate(instance=valid_minimal_manifest, schema=schema)
    
    @pytest.mark.parametrize("api_version", [
        "2.0",  # Future version
        "1",  # Wrong format
        1.0,  # Number instead of string
    ])
    def test_invalid_api_version(self, schema, valid_minimal_manifest, api_version):
        """Invalid API versions should fail."""
        valid_minimal_manifest["api_version"] = api_version
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)


class TestOptionalFields:
    """Test optional field validation."""
    
    def test_author_field(self, schema, valid_minimal_manifest):
        """Author field with valid structure should pass."""
        valid_minimal_manifest["author"] = {
            "name": "Test Author",
            "email": "test@example.com",
            "url": "https://example.com"
        }
        validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_author_missing_name(self, schema, valid_minimal_manifest):
        """Author without name should fail."""
        valid_minimal_manifest["author"] = {
            "email": "test@example.com"
        }
        with pytest.raises(ValidationError, match="'name' is a required property"):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_dependencies_field(self, schema, valid_minimal_manifest):
        """Dependencies field should pass with valid structure."""
        valid_minimal_manifest["dependencies"] = {
            "core_version": ">=1.0.0",
            "python_version": ">=3.10",
            "plugins": {
                "plugin-source-other": ">=1.0.0"
            },
            "system": [
                {"name": "redis", "version": ">=6.0"}
            ]
        }
        validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_capabilities_field(self, schema, valid_minimal_manifest):
        """Capabilities field should pass with valid values."""
        valid_minimal_manifest["capabilities"] = [
            "incremental_scraping",
            "real_time_updates",
            "batch_processing"
        ]
        validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_invalid_capability(self, schema, valid_minimal_manifest):
        """Invalid capability should fail."""
        valid_minimal_manifest["capabilities"] = [
            "invalid_capability"  # Not in enum
        ]
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_resources_field(self, schema, valid_minimal_manifest):
        """Resources field should pass with valid limits."""
        valid_minimal_manifest["resources"] = {
            "memory_mb": 512,
            "cpu_cores": 1.5,
            "disk_mb": 1000,
            "network": "medium"
        }
        validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_resources_exceed_limits(self, schema, valid_minimal_manifest):
        """Resources exceeding limits should fail."""
        valid_minimal_manifest["resources"] = {
            "memory_mb": 20000  # Exceeds 16384 limit
        }
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_entrypoint_field(self, schema, valid_minimal_manifest):
        """Entrypoint field should pass with valid structure."""
        valid_minimal_manifest["entrypoint"] = {
            "module": "my_plugin.main",
            "class": "MyPlugin"
        }
        validate(instance=valid_minimal_manifest, schema=schema)
    
    def test_entrypoint_invalid_module(self, schema, valid_minimal_manifest):
        """Entrypoint with invalid module name should fail."""
        valid_minimal_manifest["entrypoint"] = {
            "module": "Invalid-Module",  # Hyphens not allowed
            "class": "MyPlugin"
        }
        with pytest.raises(ValidationError):
            validate(instance=valid_minimal_manifest, schema=schema)


class TestComplexManifests:
    """Test complex real-world manifests."""
    
    def test_full_source_plugin_manifest(self, schema):
        """Full source plugin manifest should pass."""
        manifest = {
            "id": "plugin-source-avito",
            "name": "Avito Scraper",
            "version": "1.2.3",
            "type": "source",
            "api_version": "1.0",
            "description": "Scrapes listings from Avito.ru",
            "author": {
                "name": "Test Team",
                "email": "team@example.com",
                "url": "https://example.com"
            },
            "license": "MIT",
            "repository": "https://github.com/test/plugin-source-avito",
            "dependencies": {
                "core_version": ">=1.0.0,<2.0.0",
                "python_version": ">=3.10",
                "plugins": {
                    "plugin-processing-normalizer": ">=1.0.0"
                },
                "system": [
                    {"name": "redis", "version": ">=6.0"}
                ]
            },
            "config": {
                "schema": "config.schema.json",
                "required_keys": ["regions", "update_interval"],
                "defaults": {
                    "regions": ["moscow"],
                    "update_interval": 3600
                }
            },
            "capabilities": [
                "incremental_scraping",
                "real_time_updates",
                "batch_processing"
            ],
            "resources": {
                "memory_mb": 512,
                "cpu_cores": 1,
                "disk_mb": 100,
                "network": "medium"
            },
            "hooks": {
                "on_install": "scripts/setup.sh",
                "on_enable": "scripts/start.sh"
            },
            "metrics": [
                {
                    "name": "listings_scraped_total",
                    "type": "counter",
                    "description": "Total listings scraped",
                    "labels": ["region"]
                }
            ],
            "entrypoint": {
                "module": "avito_scraper.plugin",
                "class": "AvitoSourcePlugin"
            },
            "tags": ["avito", "russia", "scraper"]
        }
        validate(instance=manifest, schema=schema)


class TestFixtureFiles:
    """Test validation against fixture files."""
    
    def test_valid_fixture(self, schema):
        """Valid fixture file should pass."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "plugins" / "valid_source_plugin.yaml"
        with open(fixture_path) as f:
            manifest = yaml.safe_load(f)
        validate(instance=manifest, schema=schema)
    
    def test_invalid_fixtures(self, schema):
        """Invalid fixture files should fail."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "plugins"
        invalid_files = [
            "invalid_missing_fields.yaml",
            "invalid_id_pattern.yaml",
            "invalid_version.yaml"
        ]
        
        for filename in invalid_files:
            fixture_path = fixtures_dir / filename
            with open(fixture_path) as f:
                manifest = yaml.safe_load(f)
            with pytest.raises(ValidationError):
                validate(instance=manifest, schema=schema)
