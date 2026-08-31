# tests/test_graph_algorithms_dfs.py
"""Iterative DFS - no stack overflow on deep graphs.

Split out of test_dxf_security_patch.py.
"""

import pytest

from app.cam.graph_algorithms import (
    build_adjacency_map_safe,
    find_cycles_iterative,
    GraphOverflowError,
)

# =============================================================================
# Iterative DFS (no stack overflow)
# =============================================================================

class TestIterativeDFS:
    """Test iterative DFS prevents stack overflow."""
    
    def test_find_simple_cycle(self):
        """Should find a simple triangle cycle."""
        # Triangle: 0-1-2-0
        adjacency = {
            0: [1, 2],
            1: [0, 2],
            2: [0, 1],
        }
        
        cycles = find_cycles_iterative(adjacency, [None, None, None])
        
        assert len(cycles) > 0
        assert 3 in [len(c) for c in cycles]  # Found triangle
    
    def test_handle_deep_graph(self):
        """Should handle deep graphs without stack overflow."""
        # Create a long chain: 0-1-2-3-...-999-0
        n = 1000
        adjacency = {i: [i+1] for i in range(n-1)}
        adjacency[n-1] = [0]  # Close the loop
        adjacency[0].append(n-1)  # Bidirectional
        
        try:
            cycles = find_cycles_iterative(adjacency, [None] * n, max_depth=1500)
            assert len(cycles) > 0  # Should find the cycle
        except GraphOverflowError:
            pytest.fail("Should not overflow on valid graph")
    
    def test_enforce_depth_limit(self):
        """Should stop at max depth to prevent infinite loops."""
        # Pathological graph with many paths
        adjacency = {i: list(range(i+1, min(i+10, 100))) for i in range(100)}
        
        # Should complete without hanging (depth limit prevents explosion)
        cycles = find_cycles_iterative(adjacency, [None] * 100, max_depth=50)
        # May or may not find cycles, but shouldn't hang
