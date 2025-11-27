"""
Semantic Versioning (SemVer) implementation.

Provides version parsing, comparison, and constraint matching according to
the Semantic Versioning 2.0.0 specification (https://semver.org/).

Supports version constraints:
- Exact: "1.2.3"
- Caret: "^1.2.3" (compatible with 1.x.x, >=1.2.3 <2.0.0)
- Tilde: "~1.2.3" (compatible with 1.2.x, >=1.2.3 <1.3.0)
- Greater/Less: ">=1.2.3", "<=2.0.0", ">1.0.0", "<2.0.0"
- Range: ">=1.2.3 <2.0.0"
- Wildcard: "1.2.*", "1.*"

Author: RealEstatesAntiFraud Core Team
"""

import re
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


class VersionError(Exception):
    """Base exception for version-related errors."""
    pass


class InvalidVersionError(VersionError):
    """Raised when version string is invalid."""
    pass


class InvalidConstraintError(VersionError):
    """Raised when version constraint is invalid."""
    pass


class IncompatibleVersionError(VersionError):
    """Raised when version doesn't satisfy constraint."""
    pass


@dataclass(frozen=True)
class Version:
    """
    Represents a semantic version (major.minor.patch).
    
    Follows SemVer 2.0.0 specification.
    Immutable and hashable for use in sets/dicts.
    """
    
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    # Version regex pattern (SemVer 2.0.0)
    _VERSION_PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )
    
    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """
        Parse version string into Version object.
        
        Args:
            version_str: Version string (e.g., "1.2.3", "2.0.0-alpha.1+build.123")
            
        Returns:
            Version object
            
        Raises:
            InvalidVersionError: If version string is invalid
        """
        if not isinstance(version_str, str):
            raise InvalidVersionError(f"Version must be string, got {type(version_str)}")
        
        version_str = version_str.strip()
        
        # Remove 'v' prefix if present
        if version_str.startswith('v'):
            version_str = version_str[1:]
        
        match = cls._VERSION_PATTERN.match(version_str)
        if not match:
            raise InvalidVersionError(f"Invalid version string: '{version_str}'")
        
        groups = match.groupdict()
        
        return cls(
            major=int(groups['major']),
            minor=int(groups['minor']),
            patch=int(groups['patch']),
            prerelease=groups.get('prerelease'),
            build=groups.get('build')
        )
    
    def __str__(self) -> str:
        """String representation (e.g., '1.2.3')."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"Version('{self}')"
    
    def __lt__(self, other: "Version") -> bool:
        """Less than comparison."""
        if not isinstance(other, Version):
            return NotImplemented
        
        # Compare major.minor.patch
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)
        
        if self_tuple != other_tuple:
            return self_tuple < other_tuple
        
        # If base versions equal, compare prerelease
        # Version without prerelease > version with prerelease
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False  # self > other
        if other.prerelease is None:
            return True  # self < other
        
        # Compare prerelease lexicographically
        return self._compare_prerelease(self.prerelease, other.prerelease) < 0
    
    def __le__(self, other: "Version") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __gt__(self, other: "Version") -> bool:
        """Greater than comparison."""
        if not isinstance(other, Version):
            return NotImplemented
        return not self <= other
    
    def __ge__(self, other: "Version") -> bool:
        """Greater than or equal comparison."""
        return not self < other
    
    def __eq__(self, other: object) -> bool:
        """Equality comparison (ignores build metadata per SemVer spec)."""
        if not isinstance(other, Version):
            return NotImplemented
        
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    def __hash__(self) -> int:
        """Hash (excludes build metadata per SemVer spec)."""
        return hash((self.major, self.minor, self.patch, self.prerelease))
    
    @staticmethod
    def _compare_prerelease(pre1: str, pre2: str) -> int:
        """
        Compare prerelease versions.
        
        Returns:
            -1 if pre1 < pre2, 0 if equal, 1 if pre1 > pre2
        """
        parts1 = pre1.split('.')
        parts2 = pre2.split('.')
        
        for p1, p2 in zip(parts1, parts2):
            # Try numeric comparison first
            try:
                n1, n2 = int(p1), int(p2)
                if n1 != n2:
                    return -1 if n1 < n2 else 1
            except ValueError:
                # Alphanumeric comparison
                if p1 != p2:
                    return -1 if p1 < p2 else 1
        
        # Shorter version is smaller
        if len(parts1) != len(parts2):
            return -1 if len(parts1) < len(parts2) else 1
        
        return 0
    
    @property
    def core(self) -> Tuple[int, int, int]:
        """Get core version tuple (major, minor, patch)."""
        return (self.major, self.minor, self.patch)
    
    def is_prerelease(self) -> bool:
        """Check if this is a prerelease version."""
        return self.prerelease is not None


class VersionConstraint:
    """
    Represents a version constraint for dependency checking.
    
    Supports multiple constraint formats:
    - Exact: "1.2.3"
    - Caret: "^1.2.3" (>=1.2.3 <2.0.0)
    - Tilde: "~1.2.3" (>=1.2.3 <1.3.0)
    - Comparison: ">=1.2.3", "<=2.0.0", ">1.0.0", "<2.0.0"
    - Range: ">=1.2.3 <2.0.0"
    - Wildcard: "1.2.*", "1.*", "*"
    """
    
    # Constraint patterns
    _CARET_PATTERN = re.compile(r'^\^(.+)$')
    _TILDE_PATTERN = re.compile(r'^~(.+)$')
    _COMPARISON_PATTERN = re.compile(r'^(>=|<=|>|<|=)(.+)$')
    _WILDCARD_PATTERN = re.compile(r'^(\d+|\*)\.(\d+|\*)\.?(\d+|\*)?$')
    
    def __init__(self, constraint_str: str):
        """
        Initialize version constraint.
        
        Args:
            constraint_str: Constraint string (e.g., "^1.2.3", ">=1.0.0 <2.0.0")
            
        Raises:
            InvalidConstraintError: If constraint is invalid
        """
        self.original = constraint_str.strip()
        self._constraints: List[Tuple[str, Version]] = []
        
        try:
            self._parse(self.original)
        except Exception as e:
            raise InvalidConstraintError(f"Invalid constraint '{constraint_str}': {e}")
    
    def _parse(self, constraint_str: str) -> None:
        """Parse constraint string into internal representation."""
        # Handle range (space-separated constraints like ">=1.0.0 <2.0.0")
        # Use regex to split by comparison operators while keeping them
        import re
        
        # Pattern to split on operators while keeping them
        pattern = r'(>=|<=|>|<|=|\^|~)'
        parts = re.split(pattern, constraint_str)
        
        # Filter empty parts and reconstruct operator+version pairs
        clean_parts = [p.strip() for p in parts if p.strip()]
        
        # If we have multiple operator-version pairs, parse each
        if len(clean_parts) > 2:
            i = 0
            while i < len(clean_parts):
                if clean_parts[i] in ['>=', '<=', '>', '<', '=', '^', '~']:
                    # Operator followed by version
                    if i + 1 < len(clean_parts):
                        pair = clean_parts[i] + clean_parts[i + 1]
                        self._parse_single(pair)
                        i += 2
                    else:
                        raise InvalidConstraintError(f"Operator without version: {clean_parts[i]}")
                else:
                    # Just a version (exact match)
                    self._parse_single(clean_parts[i])
                    i += 1
        else:
            # Single constraint
            self._parse_single(constraint_str)
    
    def _parse_single(self, constraint_str: str) -> None:
        """Parse single constraint."""
        # Wildcard
        if '*' in constraint_str:
            self._parse_wildcard(constraint_str)
            return
        
        # Caret (^)
        match = self._CARET_PATTERN.match(constraint_str)
        if match:
            self._parse_caret(match.group(1))
            return
        
        # Tilde (~)
        match = self._TILDE_PATTERN.match(constraint_str)
        if match:
            self._parse_tilde(match.group(1))
            return
        
        # Comparison (>=, <=, >, <, =)
        match = self._COMPARISON_PATTERN.match(constraint_str)
        if match:
            op, version_str = match.groups()
            version = Version.parse(version_str)
            self._constraints.append((op, version))
            return
        
        # Exact version
        version = Version.parse(constraint_str)
        self._constraints.append(('=', version))
    
    def _parse_caret(self, version_str: str) -> None:
        """Parse caret constraint (^1.2.3 -> >=1.2.3 <2.0.0)."""
        version = Version.parse(version_str)
        self._constraints.append(('>=', version))
        
        # Next major version
        next_major = Version(version.major + 1, 0, 0)
        self._constraints.append(('<', next_major))
    
    def _parse_tilde(self, version_str: str) -> None:
        """Parse tilde constraint (~1.2.3 -> >=1.2.3 <1.3.0)."""
        version = Version.parse(version_str)
        self._constraints.append(('>=', version))
        
        # Next minor version
        next_minor = Version(version.major, version.minor + 1, 0)
        self._constraints.append(('<', next_minor))
    
    def _parse_wildcard(self, wildcard_str: str) -> None:
        """Parse wildcard constraint (1.2.* -> >=1.2.0 <1.3.0)."""
        # * matches any version
        if wildcard_str.strip() == '*':
            self._constraints.append(('>=', Version(0, 0, 0)))
            return
        
        match = self._WILDCARD_PATTERN.match(wildcard_str)
        if not match:
            raise InvalidConstraintError(f"Invalid wildcard: '{wildcard_str}'")
        
        major_str, minor_str, patch_str = match.groups()
        
        # * matches any version (already handled above, but keep for safety)
        if major_str == '*':
            self._constraints.append(('>=', Version(0, 0, 0)))
            return
        
        major = int(major_str)
        
        # 1.* -> >=1.0.0 <2.0.0
        if minor_str == '*':
            self._constraints.append(('>=', Version(major, 0, 0)))
            self._constraints.append(('<', Version(major + 1, 0, 0)))
            return
        
        minor = int(minor_str)
        
        # 1.2.* -> >=1.2.0 <1.3.0
        if not patch_str or patch_str == '*':
            self._constraints.append(('>=', Version(major, minor, 0)))
            self._constraints.append(('<', Version(major, minor + 1, 0)))
            return
        
        # No wildcard, treat as exact
        patch = int(patch_str)
        self._constraints.append(('=', Version(major, minor, patch)))
    
    def satisfies(self, version: Version) -> bool:
        """
        Check if version satisfies this constraint.
        
        Args:
            version: Version to check
            
        Returns:
            True if version satisfies constraint
        """
        for op, constraint_version in self._constraints:
            if not self._check_operator(version, op, constraint_version):
                return False
        return True
    
    @staticmethod
    def _check_operator(version: Version, op: str, constraint_version: Version) -> bool:
        """Check if version satisfies operator constraint."""
        if op == '=':
            return version == constraint_version
        elif op == '>':
            return version > constraint_version
        elif op == '<':
            return version < constraint_version
        elif op == '>=':
            return version >= constraint_version
        elif op == '<=':
            return version <= constraint_version
        else:
            raise InvalidConstraintError(f"Unknown operator: '{op}'")
    
    def __str__(self) -> str:
        """String representation."""
        return self.original
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"VersionConstraint('{self.original}')"


def check_compatibility(
    version: str,
    constraint: str,
    context: Optional[str] = None
) -> bool:
    """
    Check if version satisfies constraint.
    
    Args:
        version: Version string to check
        constraint: Constraint string
        context: Optional context for error messages (e.g., plugin name)
        
    Returns:
        True if compatible
        
    Raises:
        IncompatibleVersionError: If incompatible
        InvalidVersionError: If version is invalid
        InvalidConstraintError: If constraint is invalid
    """
    try:
        ver = Version.parse(version)
        cons = VersionConstraint(constraint)
        
        if not cons.satisfies(ver):
            ctx = f" ({context})" if context else ""
            raise IncompatibleVersionError(
                f"Version {version} does not satisfy constraint {constraint}{ctx}"
            )
        
        logger.debug(f"Version {version} satisfies {constraint}")
        return True
        
    except (InvalidVersionError, InvalidConstraintError) as e:
        logger.error(f"Version check failed: {e}")
        raise
