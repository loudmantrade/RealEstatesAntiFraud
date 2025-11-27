"""
Unit tests for DependencyGraph

Tests:
- Adding/removing plugins
- Building DAG
- Topological sorting
- Cycle detection
- Missing dependency detection
- DOT export
"""

import pytest
from core.dependency_graph import (
    DependencyGraph,
    PluginNode,
    CyclicDependencyError,
    MissingDependencyError
)


class TestPluginNode:
    """Test PluginNode dataclass."""
    
    def test_plugin_node_creation(self):
        """Test creating a plugin node."""
        node = PluginNode(
            plugin_id="plugin-source-test",
            version="1.0.0",
            dependencies=["plugin-processing-dep"]
        )
        assert node.plugin_id == "plugin-source-test"
        assert node.version == "1.0.0"
        assert node.dependencies == ["plugin-processing-dep"]
    
    def test_plugin_node_equality(self):
        """Test node equality based on plugin_id."""
        node1 = PluginNode("plugin-a", "1.0.0", [])
        node2 = PluginNode("plugin-a", "2.0.0", ["dep"])
        node3 = PluginNode("plugin-b", "1.0.0", [])
        
        assert node1 == node2  # Same ID, different version/deps
        assert node1 != node3  # Different ID
    
    def test_plugin_node_hashable(self):
        """Test nodes can be used in sets/dicts."""
        node1 = PluginNode("plugin-a", "1.0.0", [])
        node2 = PluginNode("plugin-a", "2.0.0", [])
        
        nodes_set = {node1, node2}
        assert len(nodes_set) == 1  # Same hash due to same ID


class TestDependencyGraphBasics:
    """Test basic graph operations."""
    
    def test_empty_graph(self):
        """Test creating empty graph."""
        graph = DependencyGraph()
        assert len(graph) == 0

    def test_add_plugin(self):
        """Test adding plugins to graph."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        assert len(graph) == 2
        assert "plugin-a" in graph
        assert "plugin-b" in graph

    def test_add_duplicate_plugin(self):
        """Test adding duplicate plugin raises error."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        
        with pytest.raises(ValueError, match="already exists"):
            graph.add_plugin("plugin-a", "2.0.0", [])

    def test_remove_plugin(self):
        """Test removing plugin from graph."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        graph.remove_plugin("plugin-b")
        assert len(graph) == 1
        assert "plugin-a" in graph
        assert "plugin-b" not in graph

    def test_remove_nonexistent_plugin(self):
        """Test removing nonexistent plugin raises error."""
        graph = DependencyGraph()
        
        with pytest.raises(KeyError, match="not found"):
            graph.remove_plugin("plugin-a")

    def test_has_plugin(self):
        """Test checking plugin existence."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        
        assert graph.has_plugin("plugin-a")
        assert not graph.has_plugin("plugin-b")

    def test_get_dependencies(self):
        """Test retrieving plugin dependencies."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-a", "plugin-b"])
        
        assert graph.get_dependencies("plugin-a") == []
        assert graph.get_dependencies("plugin-b") == ["plugin-a"]
        assert set(graph.get_dependencies("plugin-c")) == {"plugin-a", "plugin-b"}

    def test_get_dependencies_nonexistent(self):
        """Test getting dependencies of nonexistent plugin."""
        graph = DependencyGraph()
        
        with pytest.raises(KeyError, match="not found"):
            graph.get_dependencies("plugin-a")

    def test_get_dependents(self):
        """Test retrieving plugins that depend on this plugin."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-a"])
        
        dependents = set(graph.get_dependents("plugin-a"))
        assert dependents == {"plugin-b", "plugin-c"}
        assert graph.get_dependents("plugin-b") == []

    def test_get_dependents_nonexistent(self):
        """Test getting dependents of nonexistent plugin."""
        graph = DependencyGraph()
        
        with pytest.raises(KeyError, match="not found"):
            graph.get_dependents("plugin-a")


class TestDependencyValidation:
    """Test dependency validation."""
    
    def test_validate_dependencies_success(self):
        """Test validation passes when all dependencies exist."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        # Should not raise
        graph.validate_dependencies()

    def test_validate_missing_dependencies(self):
        """Test validation fails when dependencies missing."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a", "plugin-c"])
        
        with pytest.raises(MissingDependencyError) as exc_info:
            graph.validate_dependencies()
        
        assert exc_info.value.plugin_id == "plugin-b"
        assert set(exc_info.value.missing_deps) == {"plugin-a", "plugin-c"}


class TestCycleDetection:
    """Test circular dependency detection."""
    
    def test_detect_no_cycle(self):
        """Test no cycle in valid DAG."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-b"])
        
        assert graph.detect_cycle() is None

    def test_detect_self_cycle(self):
        """Test detection of self-referencing cycle."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", ["plugin-a"])
        
        cycle = graph.detect_cycle()
        assert cycle is not None
        assert cycle == ["plugin-a"]

    def test_detect_simple_cycle(self):
        """Test detection of A -> B -> A cycle."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", ["plugin-b"])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        cycle = graph.detect_cycle()
        assert cycle is not None
        assert set(cycle) == {"plugin-a", "plugin-b"}

    def test_detect_complex_cycle(self):
        """Test detection of A -> B -> C -> A cycle."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", ["plugin-b"])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-c"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-a"])
        
        cycle = graph.detect_cycle()
        assert cycle is not None
        assert set(cycle) == {"plugin-a", "plugin-b", "plugin-c"}

    def test_detect_cycle_with_independent_nodes(self):
        """Test cycle detection with independent nodes."""
        graph = DependencyGraph()
        # Independent chain
        graph.add_plugin("plugin-x", "1.0.0", [])
        graph.add_plugin("plugin-y", "1.0.0", ["plugin-x"])
        # Cycle
        graph.add_plugin("plugin-a", "1.0.0", ["plugin-b"])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        cycle = graph.detect_cycle()
        assert cycle is not None
        assert set(cycle) == {"plugin-a", "plugin-b"}


class TestGraphBuilding:
    """Test graph building and validation."""
    
    def test_build_valid_graph(self):
        """Test building valid DAG."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-b"])
        
        # Should not raise
        graph.build()

    def test_build_fails_missing_deps(self):
        """Test build fails with missing dependencies."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])

