"""
Unit tests for Semantic Versioning module.

Tests version parsing, comparison, and constraint matching.
"""

import pytest

from core.utils.semver import (IncompatibleVersionError,
                               InvalidConstraintError, InvalidVersionError,
                               Version, VersionConstraint, VersionError,
                               check_compatibility)


class TestVersionParsing:
    """Test version string parsing."""

    def test_parse_simple_version(self):
        """Test parsing simple version."""
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease is None
        assert v.build is None

    def test_parse_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        v = Version.parse("v2.0.0")
        assert v.major == 2
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_with_prerelease(self):
        """Test parsing version with prerelease."""
        v = Version.parse("1.0.0-alpha.1")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0
        assert v.prerelease == "alpha.1"

    def test_parse_with_build(self):
        """Test parsing version with build metadata."""
        v = Version.parse("1.0.0+build.123")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0
        assert v.build == "build.123"

    def test_parse_with_prerelease_and_build(self):
        """Test parsing version with both prerelease and build."""
        v = Version.parse("2.1.0-beta.2+sha.5114f85")
        assert v.major == 2
        assert v.minor == 1
        assert v.patch == 0
        assert v.prerelease == "beta.2"
        assert v.build == "sha.5114f85"

    def test_parse_invalid_version_raises_error(self):
        """Test parsing invalid version raises error."""
        with pytest.raises(InvalidVersionError):
            Version.parse("1.2")

        with pytest.raises(InvalidVersionError):
            Version.parse("abc")

        with pytest.raises(InvalidVersionError):
            Version.parse("1.2.3.4")

    def test_parse_non_string_raises_error(self):
        """Test parsing non-string raises error."""
        with pytest.raises(InvalidVersionError):
            Version.parse(123)


class TestVersionComparison:
    """Test version comparison operations."""

    def test_equal_versions(self):
        """Test equality comparison."""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.3")
        assert v1 == v2
        assert not (v1 != v2)

    def test_different_versions(self):
        """Test inequality."""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.4")
        assert v1 != v2
        assert not (v1 == v2)

    def test_less_than(self):
        """Test less than comparison."""
        assert Version.parse("1.2.3") < Version.parse("1.2.4")
        assert Version.parse("1.2.3") < Version.parse("1.3.0")
        assert Version.parse("1.2.3") < Version.parse("2.0.0")

    def test_greater_than(self):
        """Test greater than comparison."""
        assert Version.parse("2.0.0") > Version.parse("1.9.9")
        assert Version.parse("1.3.0") > Version.parse("1.2.9")
        assert Version.parse("1.2.4") > Version.parse("1.2.3")

    def test_less_than_or_equal(self):
        """Test less than or equal."""
        assert Version.parse("1.2.3") <= Version.parse("1.2.3")
        assert Version.parse("1.2.3") <= Version.parse("1.2.4")

    def test_greater_than_or_equal(self):
        """Test greater than or equal."""
        assert Version.parse("1.2.3") >= Version.parse("1.2.3")
        assert Version.parse("1.2.4") >= Version.parse("1.2.3")

    def test_prerelease_comparison(self):
        """Test prerelease version comparison."""
        # 1.0.0-alpha < 1.0.0
        assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0")

        # 1.0.0-alpha < 1.0.0-beta
        assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0-beta")

        # 1.0.0-beta.1 < 1.0.0-beta.2
        assert Version.parse("1.0.0-beta.1") < Version.parse("1.0.0-beta.2")

    def test_build_metadata_ignored_in_comparison(self):
        """Test build metadata is ignored per SemVer spec."""
        v1 = Version.parse("1.0.0+build.1")
        v2 = Version.parse("1.0.0+build.2")
        assert v1 == v2


class TestVersionString:
    """Test version string representation."""

    def test_str_simple(self):
        """Test string representation of simple version."""
        v = Version.parse("1.2.3")
        assert str(v) == "1.2.3"

    def test_str_with_prerelease(self):
        """Test string with prerelease."""
        v = Version.parse("1.0.0-alpha.1")
        assert str(v) == "1.0.0-alpha.1"

    def test_str_with_build(self):
        """Test string with build."""
        v = Version.parse("1.0.0+build.123")
        assert str(v) == "1.0.0+build.123"

    def test_str_with_both(self):
        """Test string with prerelease and build."""
        v = Version.parse("2.1.0-beta.2+sha.5114f85")
        assert str(v) == "2.1.0-beta.2+sha.5114f85"

    def test_repr(self):
        """Test repr."""
        v = Version.parse("1.2.3")
        assert repr(v) == "Version('1.2.3')"


class TestVersionProperties:
    """Test version properties and methods."""

    def test_core_property(self):
        """Test core tuple property."""
        v = Version.parse("1.2.3-alpha+build")
        assert v.core == (1, 2, 3)

    def test_is_prerelease(self):
        """Test prerelease check."""
        assert Version.parse("1.0.0-alpha").is_prerelease()
        assert not Version.parse("1.0.0").is_prerelease()

    def test_hashable(self):
        """Test versions are hashable."""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.3")
        versions_set = {v1, v2}
        assert len(versions_set) == 1


class TestVersionConstraintExact:
    """Test exact version constraints."""

    def test_exact_match(self):
        """Test exact version match."""
        constraint = VersionConstraint("1.2.3")
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert not constraint.satisfies(Version.parse("1.2.4"))

    def test_exact_with_equals(self):
        """Test exact with = operator."""
        constraint = VersionConstraint("=1.2.3")
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert not constraint.satisfies(Version.parse("1.2.4"))


class TestVersionConstraintCaret:
    """Test caret (^) constraints."""

    def test_caret_patch_updates(self):
        """Test caret allows patch updates."""
        constraint = VersionConstraint("^1.2.3")
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert constraint.satisfies(Version.parse("1.2.4"))
        assert constraint.satisfies(Version.parse("1.9.9"))

    def test_caret_blocks_major_updates(self):
        """Test caret blocks major updates."""
        constraint = VersionConstraint("^1.2.3")
        assert not constraint.satisfies(Version.parse("2.0.0"))
        assert not constraint.satisfies(Version.parse("0.9.9"))

    def test_caret_zero_major(self):
        """Test caret with 0.x version."""
        constraint = VersionConstraint("^0.2.3")
        assert constraint.satisfies(Version.parse("0.2.3"))
        assert constraint.satisfies(Version.parse("0.9.9"))
        assert not constraint.satisfies(Version.parse("1.0.0"))


class TestVersionConstraintTilde:
    """Test tilde (~) constraints."""

    def test_tilde_patch_updates(self):
        """Test tilde allows patch updates."""
        constraint = VersionConstraint("~1.2.3")
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert constraint.satisfies(Version.parse("1.2.4"))
        assert constraint.satisfies(Version.parse("1.2.9"))

    def test_tilde_blocks_minor_updates(self):
        """Test tilde blocks minor updates."""
        constraint = VersionConstraint("~1.2.3")
        assert not constraint.satisfies(Version.parse("1.3.0"))
        assert not constraint.satisfies(Version.parse("2.0.0"))


class TestVersionConstraintComparison:
    """Test comparison constraints (>, <, >=, <=)."""

    def test_greater_than(self):
        """Test > constraint."""
        constraint = VersionConstraint(">1.2.3")
        assert constraint.satisfies(Version.parse("1.2.4"))
        assert constraint.satisfies(Version.parse("2.0.0"))
        assert not constraint.satisfies(Version.parse("1.2.3"))
        assert not constraint.satisfies(Version.parse("1.2.2"))

    def test_less_than(self):
        """Test < constraint."""
        constraint = VersionConstraint("<2.0.0")
        assert constraint.satisfies(Version.parse("1.9.9"))
        assert constraint.satisfies(Version.parse("1.0.0"))
        assert not constraint.satisfies(Version.parse("2.0.0"))
        assert not constraint.satisfies(Version.parse("2.1.0"))

    def test_greater_or_equal(self):
        """Test >= constraint."""
        constraint = VersionConstraint(">=1.2.3")
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert constraint.satisfies(Version.parse("1.2.4"))
        assert not constraint.satisfies(Version.parse("1.2.2"))

    def test_less_or_equal(self):
        """Test <= constraint."""
        constraint = VersionConstraint("<=2.0.0")
        assert constraint.satisfies(Version.parse("2.0.0"))
        assert constraint.satisfies(Version.parse("1.9.9"))
        assert not constraint.satisfies(Version.parse("2.0.1"))


class TestVersionConstraintRange:
    """Test range constraints (multiple conditions)."""

    def test_range_constraint(self):
        """Test range with multiple conditions."""
        constraint = VersionConstraint(">=1.2.3 <2.0.0")
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert constraint.satisfies(Version.parse("1.9.9"))
        assert not constraint.satisfies(Version.parse("1.2.2"))
        assert not constraint.satisfies(Version.parse("2.0.0"))

    def test_complex_range(self):
        """Test complex range."""
        constraint = VersionConstraint(">1.0.0 <=1.5.0")
        assert constraint.satisfies(Version.parse("1.2.0"))
        assert constraint.satisfies(Version.parse("1.5.0"))
        assert not constraint.satisfies(Version.parse("1.0.0"))
        assert not constraint.satisfies(Version.parse("1.5.1"))


class TestVersionConstraintWildcard:
    """Test wildcard (*) constraints."""

    def test_wildcard_all(self):
        """Test * matches all versions."""
        constraint = VersionConstraint("*")
        assert constraint.satisfies(Version.parse("0.0.1"))
        assert constraint.satisfies(Version.parse("1.2.3"))
        assert constraint.satisfies(Version.parse("99.99.99"))

    def test_wildcard_major(self):
        """Test major.* constraint."""
        constraint = VersionConstraint("1.*")
        assert constraint.satisfies(Version.parse("1.0.0"))
        assert constraint.satisfies(Version.parse("1.9.9"))
        assert not constraint.satisfies(Version.parse("2.0.0"))
        assert not constraint.satisfies(Version.parse("0.9.9"))

    def test_wildcard_minor(self):
        """Test major.minor.* constraint."""
        constraint = VersionConstraint("1.2.*")
        assert constraint.satisfies(Version.parse("1.2.0"))
        assert constraint.satisfies(Version.parse("1.2.9"))
        assert not constraint.satisfies(Version.parse("1.3.0"))
        assert not constraint.satisfies(Version.parse("1.1.9"))


class TestInvalidConstraints:
    """Test invalid constraint handling."""

    def test_invalid_constraint_string(self):
        """Test invalid constraint raises error."""
        with pytest.raises(InvalidConstraintError):
            VersionConstraint("invalid")

        with pytest.raises(InvalidConstraintError):
            VersionConstraint(">>1.2.3")

    def test_invalid_version_in_constraint(self):
        """Test invalid version in constraint."""
        with pytest.raises(InvalidConstraintError):
            VersionConstraint(">=abc")


class TestCheckCompatibility:
    """Test check_compatibility helper function."""

    def test_compatible_version(self):
        """Test compatible version returns True."""
        assert check_compatibility("1.2.3", "^1.2.0")
        assert check_compatibility("2.0.0", ">=1.0.0")

    def test_incompatible_version_raises_error(self):
        """Test incompatible version raises error."""
        with pytest.raises(IncompatibleVersionError):
            check_compatibility("2.0.0", "^1.0.0")

        with pytest.raises(IncompatibleVersionError):
            check_compatibility("1.0.0", ">1.5.0")

    def test_invalid_version_raises_error(self):
        """Test invalid version raises error."""
        with pytest.raises(InvalidVersionError):
            check_compatibility("invalid", "^1.0.0")

    def test_invalid_constraint_raises_error(self):
        """Test invalid constraint raises error."""
        with pytest.raises(InvalidConstraintError):
            check_compatibility("1.0.0", "invalid")

    def test_with_context(self):
        """Test context in error message."""
        try:
            check_compatibility("2.0.0", "^1.0.0", context="test-plugin")
            pytest.fail("Should have raised IncompatibleVersionError")
        except IncompatibleVersionError as e:
            assert "test-plugin" in str(e)


class TestConstraintString:
    """Test constraint string representation."""

    def test_str(self):
        """Test string representation."""
        constraint = VersionConstraint("^1.2.3")
        assert str(constraint) == "^1.2.3"

    def test_repr(self):
        """Test repr."""
        constraint = VersionConstraint(">=1.0.0")
        assert repr(constraint) == "VersionConstraint('>=1.0.0')"


class TestRealWorldScenarios:
    """Test real-world version constraint scenarios."""

    def test_plugin_dependency_scenario(self):
        """Test typical plugin dependency scenario."""
        # Plugin requires ^2.0.0 of dependency
        constraint = VersionConstraint("^2.0.0")

        # These should work
        assert constraint.satisfies(Version.parse("2.0.0"))
        assert constraint.satisfies(Version.parse("2.1.5"))
        assert constraint.satisfies(Version.parse("2.9.9"))

        # These should not
        assert not constraint.satisfies(Version.parse("1.9.9"))
        assert not constraint.satisfies(Version.parse("3.0.0"))

    def test_backwards_compatible_api(self):
        """Test backwards compatible API versioning."""
        # API version ~1.5.0 (patch updates only)
        constraint = VersionConstraint("~1.5.0")

        # Patch updates allowed
        assert constraint.satisfies(Version.parse("1.5.0"))
        assert constraint.satisfies(Version.parse("1.5.1"))
        assert constraint.satisfies(Version.parse("1.5.99"))

        # Minor/major updates blocked
        assert not constraint.satisfies(Version.parse("1.6.0"))
        assert not constraint.satisfies(Version.parse("2.0.0"))

    def test_minimum_version_requirement(self):
        """Test minimum version with upper bound."""
        # Require >=1.0.0 but <2.0.0
        constraint = VersionConstraint(">=1.0.0 <2.0.0")

        assert constraint.satisfies(Version.parse("1.0.0"))
        assert constraint.satisfies(Version.parse("1.5.0"))
        assert constraint.satisfies(Version.parse("1.99.99"))
        assert not constraint.satisfies(Version.parse("0.9.9"))
        assert not constraint.satisfies(Version.parse("2.0.0"))
