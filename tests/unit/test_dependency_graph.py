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
        
        with pytest.raises(MissingDependencyError):
            graph.build()
    
    def test_build_fails_cycle(self):
        """Test build fails with circular dependencies."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", ["plugin-b"])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        with pytest.raises(CyclicDependencyError) as exc_info:
            graph.build()
        
        assert set(exc_info.value.cycle) == {"plugin-a", "plugin-b"}


class TestTopologicalSort:
    """Test topological sorting for load order."""
    
    def test_get_load_order_requires_build(self):
        """Test get_load_order requires build() first."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        
        with pytest.raises(RuntimeError, match="must be built"):
            graph.get_load_order()
    
    def test_load_order_single_plugin(self):
        """Test load order for single plugin."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.build()
        
        order = graph.get_load_order()
        assert order == ["plugin-a"]
    
    def test_load_order_linear_chain(self):
        """Test load order for A -> B -> C."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-b"])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.build()
        
        order = graph.get_load_order()
        assert order == ["plugin-a", "plugin-b", "plugin-c"]
    
    def test_load_order_diamond(self):
        """Test load order for diamond: A -> B,C -> D."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-d", "1.0.0", ["plugin-b", "plugin-c"])
        graph.build()
        
        order = graph.get_load_order()
        # A must be first, D must be last
        assert order[0] == "plugin-a"
        assert order[3] == "plugin-d"
        # B and C can be in any order in middle
        assert set(order[1:3]) == {"plugin-b", "plugin-c"}
    
    def test_load_order_independent_plugins(self):
        """Test load order with independent plugins."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", [])
        graph.add_plugin("plugin-c", "1.0.0", [])
        graph.build()
        
        order = graph.get_load_order()
        # All independent, any order is valid
        assert set(order) == {"plugin-a", "plugin-b", "plugin-c"}
        assert len(order) == 3
    
    def test_load_order_complex_graph(self):
        """Test load order for complex dependency graph."""
        #      A
        #     / \\
        #    B   C
        #   / \\ /
        #  D   E
        #   \\ /
        #    F
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-d", "1.0.0", ["plugin-b"])
        graph.add_plugin("plugin-e", "1.0.0", ["plugin-b", "plugin-c"])
        graph.add_plugin("plugin-f", "1.0.0", ["plugin-d", "plugin-e"])
        graph.build()
        
        order = graph.get_load_order()
        
        # Verify topological properties
        pos = {plugin: i for i, plugin in enumerate(order)}
        
        # A must be before B and C
        assert pos["plugin-a"] < pos["plugin-b"]
        assert pos["plugin-a"] < pos["plugin-c"]
        
        # B must be before D and E
        assert pos["plugin-b"] < pos["plugin-d"]
        assert pos["plugin-b"] < pos["plugin-e"]
        
        # C must be before E
        assert pos["plugin-c"] < pos["plugin-e"]
        
        # D and E must be before F
        assert pos["plugin-d"] < pos["plugin-f"]
        assert pos["plugin-e"] < pos["plugin-f"]
        
        # F must be last
        assert order[-1] == "plugin-f"
    
    def test_load_order_caching(self):
        """Test load order is cached after first call."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.build()
        
        order1 = graph.get_load_order()
        order2 = graph.get_load_order()
        
        # Should return copies
        assert order1 == order2
        assert order1 is not order2


class TestDotExport:
    """Test DOT format export for visualization."""
    
    def test_export_empty_graph(self):
        """Test exporting empty graph."""
        graph = DependencyGraph()
        dot = graph.export_dot()
        
        assert "digraph PluginDependencies" in dot
        assert "rankdir=LR" in dot
    
    def test_export_single_node(self):
        """Test exporting graph with single node."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        
        dot = graph.export_dot()
        assert '"plugin-a"' in dot
        assert "v1.0.0" in dot
    
    def test_export_with_edges(self):
        """Test exporting graph with dependencies."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.add_plugin("plugin-c", "1.0.0", ["plugin-a", "plugin-b"])
        
        dot = graph.export_dot()
        
        # Check nodes
        assert '"plugin-a"' in dot
        assert '"plugin-b"' in dot
        assert '"plugin-c"' in dot
        
        # Check edges (B depends on A, C depends on A and B)
        assert '"plugin-b" -> "plugin-a"' in dot
        assert '"plugin-c" -> "plugin-a"' in dot
        assert '"plugin-c" -> "plugin-b"' in dot
    
    def test_export_valid_dot_syntax(self):
        """Test exported DOT has valid syntax."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        
        dot = graph.export_dot()
        
        # Check basic structure
        assert dot.startswith("digraph PluginDependencies {")
        assert dot.endswith("}")
        assert dot.count("{") == dot.count("}")


class TestGraphRepr:
    """Test string representation."""
    
    def test_repr_empty(self):
        """Test repr of empty graph."""
        graph = DependencyGraph()
        repr_str = repr(graph)
        
        assert "DependencyGraph" in repr_str
        assert "plugins=0" in repr_str
        assert "built=False" in repr_str
    
    def test_repr_after_build(self):
        """Test repr after building graph."""
        graph = DependencyGraph()
        graph.add_plugin("plugin-a", "1.0.0", [])
        graph.add_plugin("plugin-b", "1.0.0", ["plugin-a"])
        graph.build()
        
        repr_str = repr(graph)
        assert "plugins=2" in repr_str
        assert "built=True" in repr_str


class TestExceptionMessages:
    """Test exception messages are informative."""
    
    def test_cyclic_dependency_message(self):
        """Test CyclicDependencyError message."""
        cycle = ["plugin-a", "plugin-b", "plugin-c"]
        error = CyclicDependencyError(cycle)
        
        assert "plugin-a" in str(error)
        assert "plugin-b" in str(error)
        assert "plugin-c" in str(error)
        assert "->" in str(error)
    
    def test_missing_dependency_message(self):
        """Test MissingDependencyError message."""
        error = MissingDependencyError("plugin-b", ["plugin-a", "plugin-c"])
        
        assert "plugin-b" in str(error)
        assert "plugin-a" in str(error)
        assert "plugin-c" in str(error)
