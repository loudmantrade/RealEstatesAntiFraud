"""
Plugin manifest validation using JSON Schema.
"""
import json
from pathlib import Path
from typing import Optional

import yaml
from jsonschema import validate, ValidationError as JSONSchemaValidationError


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""
    
    def __init__(self, message: str, errors: list[str]):
        super().__init__(message)
        self.errors = errors


def validate_manifest(
    manifest_path: Path,
    schema_path: Optional[Path] = None
) -> tuple[bool, list[str]]:
    """
    Validate plugin manifest against JSON Schema.
    
    Args:
        manifest_path: Path to plugin.yaml file
        schema_path: Optional path to JSON Schema file. 
                    If None, uses default schema location.
    
    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if validation passes, False otherwise
        - error_messages: List of validation error messages (empty if valid)
    
    Example:
        >>> is_valid, errors = validate_manifest(Path("plugin.yaml"))
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
    errors = []
    
    # Load JSON Schema
    try:
        if schema_path is None:
            # Default schema location relative to this file
            schema_path = (
                Path(__file__).parent.parent.parent / 
                "schemas" / 
                "plugin-manifest-v1.schema.json"
            )
        
        with open(schema_path) as f:
            schema = json.load(f)
    except FileNotFoundError:
        return False, [f"Schema file not found: {schema_path}"]
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON Schema: {e}"]
    except Exception as e:
        return False, [f"Error loading schema: {e}"]
    
    # Load manifest YAML
    try:
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)
    except FileNotFoundError:
        return False, [f"Manifest file not found: {manifest_path}"]
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML syntax: {e}"]
    except Exception as e:
        return False, [f"Error loading manifest: {e}"]
    
    # Validate against schema
    try:
        validate(instance=manifest, schema=schema)
        return True, []
    except JSONSchemaValidationError as e:
        # Format error message with path
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        error_msg = f"Validation error at '{error_path}': {e.message}"
        
        # Add context if available
        if e.validator:
            error_msg += f" (validator: {e.validator})"
        
        errors.append(error_msg)
        
        # Add schema path for debugging
        if e.schema_path:
            schema_location = " -> ".join(str(p) for p in e.schema_path)
            errors.append(f"  Schema location: {schema_location}")
        
        return False, errors
    except Exception as e:
        return False, [f"Unexpected validation error: {e}"]


def validate_manifest_strict(manifest_path: Path) -> dict:
    """
    Validate manifest and raise exception on failure.
    
    Args:
        manifest_path: Path to plugin.yaml file
    
    Returns:
        Parsed manifest dict if validation passes
    
    Raises:
        ManifestValidationError: If validation fails
        
    Example:
        >>> try:
        ...     manifest = validate_manifest_strict(Path("plugin.yaml"))
        ...     print(f"Valid plugin: {manifest['name']}")
        ... except ManifestValidationError as e:
        ...     print(f"Validation failed: {e}")
        ...     for error in e.errors:
        ...         print(f"  - {error}")
    """
    is_valid, errors = validate_manifest(manifest_path)
    
    if not is_valid:
        error_message = f"Manifest validation failed for {manifest_path}"
        raise ManifestValidationError(error_message, errors)
    
    # Return parsed manifest
    with open(manifest_path) as f:
        return yaml.safe_load(f)


def format_validation_errors(errors: list[str]) -> str:
    """
    Format validation errors for display.
    
    Args:
        errors: List of error messages
        
    Returns:
        Formatted error string
    """
    if not errors:
        return "No errors"
    
    formatted = "Validation errors:\n"
    for i, error in enumerate(errors, 1):
        formatted += f"{i}. {error}\n"
    
    return formatted.strip()
