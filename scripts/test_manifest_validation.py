"""
Test script for validating plugin manifests against JSON Schema.
"""

import json
import sys
from pathlib import Path

import yaml

try:
    import jsonschema
    from jsonschema import ValidationError, validate
except ImportError:
    print("❌ jsonschema package not installed")
    print("Installing jsonschema...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema
    from jsonschema import ValidationError, validate


def load_schema():
    """Load JSON Schema from file."""
    schema_path = Path(__file__).parent.parent / "schemas" / "plugin-manifest-v1.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def load_manifest(manifest_path: Path):
    """Load YAML manifest."""
    with open(manifest_path) as f:
        return yaml.safe_load(f)


def validate_manifest(manifest_path: Path, schema: dict) -> tuple[bool, str]:
    """
    Validate manifest against schema.

    Returns:
        (is_valid, message)
    """
    try:
        manifest = load_manifest(manifest_path)
        validate(instance=manifest, schema=schema)
        return True, "✅ Valid"
    except ValidationError as e:
        return False, f"❌ Validation Error: {e.message}\n   Path: {list(e.path)}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def main():
    """Run validation tests."""
    print("🧪 Testing Plugin Manifest Validation\n")
    print("=" * 70)

    # Load schema
    try:
        schema = load_schema()
        print(f"✅ Loaded JSON Schema: {schema.get('title', 'Unknown')}")
        print(f"   Schema ID: {schema.get('$id', 'N/A')}")
        print()
    except Exception as e:
        print(f"❌ Failed to load schema: {e}")
        return 1

    # Find test manifests
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "plugins"
    manifest_files = sorted(fixtures_dir.glob("*.yaml"))

    if not manifest_files:
        print(f"⚠️  No test manifests found in {fixtures_dir}")
        return 1

    print(f"📁 Found {len(manifest_files)} test manifest(s)\n")

    # Validate each manifest
    results = []
    for manifest_path in manifest_files:
        print(f"Testing: {manifest_path.name}")
        is_valid, message = validate_manifest(manifest_path, schema)
        results.append((manifest_path.name, is_valid, message))
        print(f"  {message}")
        print()

    # Summary
    print("=" * 70)
    print("\n📊 Summary:\n")

    valid_count = sum(1 for _, is_valid, _ in results if is_valid)
    invalid_count = len(results) - valid_count

    print(f"Total: {len(results)}")
    print(f"✅ Valid: {valid_count}")
    print(f"❌ Invalid: {invalid_count}")
    print()

    # Expected results
    expected_valid = ["valid_source_plugin.yaml"]
    expected_invalid = ["invalid_missing_fields.yaml", "invalid_id_pattern.yaml", "invalid_version.yaml"]

    print("🎯 Expected Results Check:")
    all_correct = True

    for name, is_valid, _ in results:
        if name in expected_valid:
            if is_valid:
                print(f"  ✅ {name} - correctly validated as VALID")
            else:
                print(f"  ❌ {name} - should be VALID but got INVALID")
                all_correct = False
        elif name in expected_invalid:
            if not is_valid:
                print(f"  ✅ {name} - correctly validated as INVALID")
            else:
                print(f"  ❌ {name} - should be INVALID but got VALID")
                all_correct = False

    print()
    if all_correct:
        print("🎉 All tests passed! Schema validation works correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Review validation logic.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
