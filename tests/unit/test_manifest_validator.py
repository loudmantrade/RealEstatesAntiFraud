"""
Unit tests for manifest validation module.
"""

from pathlib import Path

import pytest

from core.validators.manifest import (ManifestValidationError,
                                      format_validation_errors,
                                      validate_manifest,
                                      validate_manifest_strict)


@pytest.fixture
def valid_manifest_path():
    """Path to valid test manifest."""
    return (
        Path(__file__).parent.parent
        / "fixtures"
        / "plugins"
        / "valid_source_plugin.yaml"
    )


@pytest.fixture
def invalid_manifest_paths():
    """Paths to invalid test manifests."""
    base = Path(__file__).parent.parent / "fixtures" / "plugins"
    return {
        "missing_fields": base / "invalid_missing_fields.yaml",
        "bad_id": base / "invalid_id_pattern.yaml",
        "bad_version": base / "invalid_version.yaml",
    }


class TestValidateManifest:
    """Test validate_manifest function."""

    def test_valid_manifest(self, valid_manifest_path):
        """Valid manifest should pass validation."""
        is_valid, errors = validate_manifest(valid_manifest_path)
        assert is_valid is True
        assert errors == []

    def test_invalid_missing_fields(self, invalid_manifest_paths):
        """Manifest with missing required fields should fail."""
        is_valid, errors = validate_manifest(invalid_manifest_paths["missing_fields"])
        assert is_valid is False
        assert len(errors) > 0
        assert "version" in errors[0].lower() or "required" in errors[0].lower()

    def test_invalid_id_pattern(self, invalid_manifest_paths):
        """Manifest with invalid ID pattern should fail."""
        is_valid, errors = validate_manifest(invalid_manifest_paths["bad_id"])
        assert is_valid is False
        assert len(errors) > 0
        assert "id" in errors[0].lower() or "match" in errors[0].lower()

    def test_invalid_version(self, invalid_manifest_paths):
        """Manifest with invalid version should fail."""
        is_valid, errors = validate_manifest(invalid_manifest_paths["bad_version"])
        assert is_valid is False
        assert len(errors) > 0
        assert "version" in errors[0].lower()

    def test_nonexistent_manifest(self):
        """Nonexistent manifest should fail with clear error."""
        is_valid, errors = validate_manifest(Path("/nonexistent/plugin.yaml"))
        assert is_valid is False
        assert len(errors) > 0
        assert "not found" in errors[0].lower()

    def test_custom_schema_path(self, valid_manifest_path):
        """Should accept custom schema path."""
        schema_path = (
            Path(__file__).parent.parent.parent
            / "schemas"
            / "plugin-manifest-v1.schema.json"
        )
        is_valid, errors = validate_manifest(
            valid_manifest_path, schema_path=schema_path
        )
        assert is_valid is True
        assert errors == []


class TestValidateManifestStrict:
    """Test validate_manifest_strict function."""

    def test_valid_manifest_returns_dict(self, valid_manifest_path):
        """Valid manifest should return parsed dict."""
        manifest = validate_manifest_strict(valid_manifest_path)
        assert isinstance(manifest, dict)
        assert "id" in manifest
        assert "name" in manifest
        assert "version" in manifest
        assert manifest["type"] == "source"

    def test_invalid_manifest_raises_exception(self, invalid_manifest_paths):
        """Invalid manifest should raise ManifestValidationError."""
        with pytest.raises(ManifestValidationError) as exc_info:
            validate_manifest_strict(invalid_manifest_paths["missing_fields"])

        error = exc_info.value
        assert len(error.errors) > 0
        assert "validation failed" in str(error).lower()

    def test_exception_contains_errors(self, invalid_manifest_paths):
        """ManifestValidationError should contain error list."""
        with pytest.raises(ManifestValidationError) as exc_info:
            validate_manifest_strict(invalid_manifest_paths["bad_id"])

        error = exc_info.value
        assert isinstance(error.errors, list)
        assert len(error.errors) > 0


class TestFormatValidationErrors:
    """Test format_validation_errors function."""

    def test_no_errors(self):
        """Empty error list should return 'No errors'."""
        result = format_validation_errors([])
        assert result == "No errors"

    def test_single_error(self):
        """Single error should be formatted with number."""
        errors = ["Field 'id' is required"]
        result = format_validation_errors(errors)
        assert "1." in result
        assert "Field 'id' is required" in result

    def test_multiple_errors(self):
        """Multiple errors should be numbered."""
        errors = [
            "Field 'id' is required",
            "Field 'version' is invalid",
            "Field 'type' must be one of: source, processing",
        ]
        result = format_validation_errors(errors)
        assert "1." in result
        assert "2." in result
        assert "3." in result
        for error in errors:
            assert error in result

    def test_format_starts_with_header(self):
        """Formatted output should start with header."""
        errors = ["Some error"]
        result = format_validation_errors(errors)
        assert result.startswith("Validation errors:")


class TestErrorMessages:
    """Test quality of error messages."""

    def test_error_includes_path(self, invalid_manifest_paths):
        """Error should include field path."""
        is_valid, errors = validate_manifest(invalid_manifest_paths["bad_id"])
        assert is_valid is False
        # Error should mention the field that failed
        assert any("id" in err.lower() for err in errors)

    def test_error_includes_validator_info(self, invalid_manifest_paths):
        """Error should include validator information."""
        is_valid, errors = validate_manifest(invalid_manifest_paths["bad_version"])
        assert is_valid is False
        # Should have descriptive error
        assert len(errors[0]) > 20  # Not just "Invalid"

    def test_yaml_syntax_error_handling(self, tmp_path):
        """Invalid YAML syntax should produce clear error."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("invalid: yaml: [unclosed")

        is_valid, errors = validate_manifest(bad_yaml)
        assert is_valid is False
        assert any("yaml" in err.lower() for err in errors)


class TestIntegrationWithSchema:
    """Test integration with actual JSON Schema."""

    def test_all_required_fields_validated(self, tmp_path):
        """Schema should validate all required fields."""
        required_fields = [
            "id",
            "name",
            "version",
            "type",
            "api_version",
            "description",
        ]

        for field in required_fields:
            # Create manifest missing one field
            manifest = tmp_path / f"missing_{field}.yaml"
            manifest_data = {
                "id": "plugin-source-test",
                "name": "Test",
                "version": "1.0.0",
                "type": "source",
                "api_version": "1.0",
                "description": "Test plugin",
            }
            del manifest_data[field]

            import yaml

            with open(manifest, "w") as f:
                yaml.dump(manifest_data, f)

            is_valid, errors = validate_manifest(manifest)
            assert is_valid is False, f"Should fail without '{field}'"
            assert any(field in err.lower() for err in errors)

    def test_optional_fields_not_required(self, tmp_path):
        """Optional fields should not be required."""
        # Minimal valid manifest
        manifest = tmp_path / "minimal.yaml"
        manifest_data = {
            "id": "plugin-source-test",
            "name": "Test Plugin",
            "version": "1.0.0",
            "type": "source",
            "api_version": "1.0",
            "description": "Test plugin",
        }

        import yaml

        with open(manifest, "w") as f:
            yaml.dump(manifest_data, f)

        is_valid, errors = validate_manifest(manifest)
        assert is_valid is True
        assert errors == []
