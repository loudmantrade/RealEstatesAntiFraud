"""
Plugin Dependency Graph

Manages plugin dependencies using Directed Acyclic Graph (DAG) with:
- Topological sorting to determine load order
- Cycle detection to prevent circular dependencies
- Dependency validation
- Graph visualization support

Author: RealEstatesAntiFraud Core Team
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from core.utils.semver import InvalidConstraintError, InvalidVersionError, Version, VersionConstraint

logger = logging.getLogger(__name__)


@dataclass
class PluginNode:
    """Represents a plugin node in the dependency graph."""

    plugin_id: str
    version: str
    dependencies: Dict[str, str]  # Map of plugin_id -> version_constraint

    def __hash__(self):
        return hash(self.plugin_id)

    def __eq__(self, other):
        if not isinstance(other, PluginNode):
            return False
        return self.plugin_id == other.plugin_id


class CyclicDependencyError(Exception):
    """Raised when a circular dependency is detected."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Cyclic dependency detected: {cycle_str}")


class MissingDependencyError(Exception):
    """Raised when a required dependency is not found."""

    def __init__(self, plugin_id: str, missing_deps: List[str]):
        self.plugin_id = plugin_id
        self.missing_deps = missing_deps
        deps_str = ", ".join(missing_deps)
        super().__init__(f"Plugin '{plugin_id}' has missing dependencies: {deps_str}")


class VersionIncompatibilityError(Exception):
    """Raised when plugin version doesn't satisfy dependency constraint."""

    def __init__(
        self,
        dependent_plugin: str,
        dependency_plugin: str,
        required_version: str,
        actual_version: str,
    ):
        self.dependent_plugin = dependent_plugin
        self.dependency_plugin = dependency_plugin
        self.required_version = required_version
        self.actual_version = actual_version
        super().__init__(
            f"Plugin '{dependent_plugin}' requires '{dependency_plugin}' "
            f"version '{required_version}', but found version '{actual_version}'"
        )


class DependencyGraph:
    """
    Manages plugin dependency graph with DAG structure.

    Features:
    - Add plugins with their dependencies
    - Build DAG and validate structure
    - Compute topological order for loading
    - Detect circular dependencies
    - Visualize graph structure

    Thread-safety: Not thread-safe. External synchronization required.
    """

    def __init__(self):
        """Initialize empty dependency graph."""
        self._nodes: Dict[str, PluginNode] = {}
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._load_order: Optional[List[str]] = None
        self._is_built = False
        logger.debug("Initialized DependencyGraph")

    def add_plugin(
        self,
        plugin_id: str,
        version: str,
        dependencies: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add a plugin node to the graph.

        Args:
            plugin_id: Unique plugin identifier
            version: Plugin version (semver)
            dependencies: Dict mapping plugin_id -> version_constraint
                         Example: {"plugin-a": "^1.0.0", "plugin-b": "~2.1.0"}

        Raises:
            ValueError: If plugin_id already exists
            InvalidVersionError: If version is invalid semver
            InvalidConstraintError: If constraint is invalid
        """
        if plugin_id in self._nodes:
            raise ValueError(f"Plugin '{plugin_id}' already exists in graph")

        # Validate version format
        try:
            Version.parse(version)
        except InvalidVersionError as e:
            raise ValueError(f"Invalid version for plugin '{plugin_id}': {e}")

        # Validate constraint formats
        deps = dependencies or {}
        for dep_id, constraint_str in deps.items():
            try:
                VersionConstraint(constraint_str)
            except InvalidConstraintError as e:
                raise ValueError(f"Invalid constraint for dependency '{dep_id}' " f"in plugin '{plugin_id}': {e}")

        node = PluginNode(plugin_id=plugin_id, version=version, dependencies=deps)

        self._nodes[plugin_id] = node

        # Build adjacency lists
        for dep_id in deps.keys():
            self._adjacency[plugin_id].add(dep_id)
            self._reverse_adjacency[dep_id].add(plugin_id)

        # Invalidate cached load order
        self._load_order = None
        self._is_built = False

        logger.debug(f"Added plugin '{plugin_id}' v{version} with {len(deps)} dependencies")

    def remove_plugin(self, plugin_id: str) -> None:
        """
        Remove a plugin from the graph.

        Args:
            plugin_id: Plugin identifier to remove

        Raises:
            KeyError: If plugin doesn't exist
        """
        if plugin_id not in self._nodes:
            raise KeyError(f"Plugin '{plugin_id}' not found in graph")

        # Remove from adjacency lists
        for dep_id in self._nodes[plugin_id].dependencies:
            self._reverse_adjacency[dep_id].discard(plugin_id)

        # Remove reverse adjacency entries
        if plugin_id in self._reverse_adjacency:
            for dependent_id in self._reverse_adjacency[plugin_id]:
                self._adjacency[dependent_id].discard(plugin_id)
            del self._reverse_adjacency[plugin_id]

        # Remove adjacency entry
        if plugin_id in self._adjacency:
            del self._adjacency[plugin_id]

        # Remove node
        del self._nodes[plugin_id]

        # Invalidate cache
        self._load_order = None
        self._is_built = False

        logger.debug(f"Removed plugin '{plugin_id}' from graph")

    def has_plugin(self, plugin_id: str) -> bool:
        """Check if plugin exists in graph."""
        return plugin_id in self._nodes

    def get_dependencies(self, plugin_id: str) -> Dict[str, str]:
        """
        Get direct dependencies of a plugin with version constraints.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Dict mapping plugin_id -> version_constraint

        Raises:
            KeyError: If plugin doesn't exist
        """
        if plugin_id not in self._nodes:
            raise KeyError(f"Plugin '{plugin_id}' not found in graph")
        return dict(self._nodes[plugin_id].dependencies)

    def get_dependents(self, plugin_id: str) -> List[str]:
        """
        Get plugins that depend on this plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of plugin IDs that depend on this plugin

        Raises:
            KeyError: If plugin doesn't exist
        """
        if plugin_id not in self._nodes:
            raise KeyError(f"Plugin '{plugin_id}' not found in graph")
        return list(self._reverse_adjacency.get(plugin_id, []))

    def validate_dependencies(self) -> None:
        """
        Validate that all dependencies exist and satisfy version constraints.

        Raises:
            MissingDependencyError: If any plugin has missing dependencies
            VersionIncompatibilityError: If version constraints are not satisfied
        """
        for plugin_id, node in self._nodes.items():
            # Check for missing dependencies
            missing = [dep_id for dep_id in node.dependencies.keys() if dep_id not in self._nodes]
            if missing:
                raise MissingDependencyError(plugin_id, missing)

            # Check version compatibility
            for dep_id, constraint_str in node.dependencies.items():
                dep_node = self._nodes[dep_id]
                dep_version = Version.parse(dep_node.version)
                constraint = VersionConstraint(constraint_str)

                if not constraint.satisfies(dep_version):
                    raise VersionIncompatibilityError(
                        dependent_plugin=plugin_id,
                        dependency_plugin=dep_id,
                        required_version=constraint_str,
                        actual_version=dep_node.version,
                    )

        logger.debug("All dependencies validated successfully")

    def detect_cycle(self) -> Optional[List[str]]:
        """
        Detect circular dependencies using DFS.

        Returns:
            List of plugin IDs forming a cycle, or None if no cycle exists
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node: WHITE for node in self._nodes}
        parent: Dict[str, Optional[str]] = {node: None for node in self._nodes}

        def dfs(node: str) -> Optional[List[str]]:
            """DFS to detect back edges (cycles)."""
            color[node] = GRAY

            for neighbor in self._adjacency.get(node, []):
                if color[neighbor] == GRAY:
                    # Back edge found - reconstruct cycle
                    cycle = [neighbor]
                    current = node
                    while current != neighbor:
                        cycle.append(current)
                        current = parent[current]
                    cycle.reverse()
                    return cycle

                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle

            color[node] = BLACK
            return None

        # Try DFS from each unvisited node
        for node in self._nodes:
            if color[node] == WHITE:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    def build(self) -> None:
        """
        Build and validate the dependency graph.

        Raises:
            MissingDependencyError: If dependencies are missing
            CyclicDependencyError: If circular dependencies exist
        """
        logger.info(f"Building dependency graph with {len(self._nodes)} plugins")

        # Validate all dependencies exist
        self.validate_dependencies()

        # Detect cycles
        cycle = self.detect_cycle()
        if cycle:
            raise CyclicDependencyError(cycle)

        self._is_built = True
        logger.info("Dependency graph built successfully")

    def get_load_order(self) -> List[str]:
        """
        Get topologically sorted plugin load order using Kahn's algorithm.

        Returns:
            List of plugin IDs in load order (dependencies first)

        Raises:
            RuntimeError: If graph hasn't been built
            CyclicDependencyError: If circular dependencies exist
        """
        if not self._is_built:
            raise RuntimeError("Graph must be built before getting load order")

        # Return cached result if available
        if self._load_order is not None:
            return self._load_order.copy()

        # Kahn's algorithm for topological sort
        in_degree: Dict[str, int] = {node: len(deps) for node, deps in self._adjacency.items()}

        # Add nodes with no dependencies
        for node in self._nodes:
            if node not in in_degree:
                in_degree[node] = 0

        # Queue of nodes with no dependencies
        queue: deque = deque([node for node, degree in in_degree.items() if degree == 0])

        result: List[str] = []

        while queue:
            # Remove node with no dependencies
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree for dependents
            for dependent in self._reverse_adjacency.get(current, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all nodes processed, there's a cycle
        if len(result) != len(self._nodes):
            # This shouldn't happen if build() was called, but double-check
            cycle = self.detect_cycle()
            raise CyclicDependencyError(cycle or ["unknown"])

        # Cache result
        self._load_order = result
        logger.debug(f"Computed load order: {' -> '.join(result)}")

        return result.copy()

    def export_dot(self) -> str:
        """
        Export graph in DOT format for Graphviz visualization.

        Returns:
            DOT format string
        """
        lines = ["digraph PluginDependencies {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded];")
        lines.append("")

        # Add nodes
        for plugin_id, node in self._nodes.items():
            label = f"{plugin_id}\\nv{node.version}"
            lines.append(f'  "{plugin_id}" [label="{label}"];')

        lines.append("")

        # Add edges (dependencies)
        for plugin_id, deps in self._adjacency.items():
            for dep_id in deps:
                lines.append(f'  "{plugin_id}" -> "{dep_id}";')

        lines.append("}")

        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of plugins in graph."""
        return len(self._nodes)

    def __contains__(self, plugin_id: str) -> bool:
        """Check if plugin exists in graph."""
        return plugin_id in self._nodes

    def __repr__(self) -> str:
        """String representation of graph."""
        return f"DependencyGraph(plugins={len(self._nodes)}, " f"built={self._is_built})"
