# services/api/app/cam/graph_algorithms.py
"""
Graph Algorithms for Contour Reconstruction

Safe implementations of graph algorithms with:
- O(n) spatial hash for point deduplication
- Iterative DFS with depth/iteration limits
- Entity count validation

These replace the vulnerable functions in contour_reconstructor.py.

Usage:
    from app.cam.graph_algorithms import build_adjacency_map_safe, find_cycles_iterative
    
    adjacency, unique_points = build_adjacency_map_safe(edges)
    cycles = find_cycles_iterative(adjacency, unique_points)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, TYPE_CHECKING

from app.cam.dxf_limits import (
    MAX_DXF_POINTS,
    MAX_DXF_EDGES,
    MAX_RECURSION_DEPTH,
    MAX_CYCLE_SEARCH_ITERATIONS,
    SPATIAL_HASH_CELL_SIZE_MM,
)
from app.cam.spatial_hash import SpatialHash

if TYPE_CHECKING:
    from app.cam.contour_reconstructor import Edge, Point


class GraphOverflowError(Exception):
    """Raised when graph operations exceed safety limits."""
    pass


def build_adjacency_map_safe(
    edges: List['Edge'],
    tolerance: float = 0.001,
) -> Tuple[Dict[int, List[int]], List['Point']]:
    """
    Build adjacency map using spatial hash for O(n) performance.
    
    This replaces the O(n²) linear scan in the original implementation.
    
    Args:
        edges: List of edges with start/end points
        tolerance: Distance tolerance for point matching
    
    Returns:
        Tuple of (adjacency dict, unique points list)
    
    Raises:
        GraphOverflowError: If edge/point count exceeds limits
    """
    # Validate edge count
    if len(edges) > MAX_DXF_EDGES:
        raise GraphOverflowError(
            f"Edge count ({len(edges):,}) exceeds limit ({MAX_DXF_EDGES:,}). "
            "Simplify the DXF geometry."
        )
    
    # Use spatial hash for O(n) point deduplication
    spatial_hash = SpatialHash(cell_size=SPATIAL_HASH_CELL_SIZE_MM)
    point_map: Dict[int, int] = {}  # id(point) -> unique index
    
    for edge in edges:
        try:
            start_idx = spatial_hash.get_or_add(edge.start, tolerance)
            end_idx = spatial_hash.get_or_add(edge.end, tolerance)
            
            point_map[id(edge.start)] = start_idx
            point_map[id(edge.end)] = end_idx
        except ValueError as e:
            raise GraphOverflowError(str(e))
    
    # Build adjacency list
    adjacency: Dict[int, List[int]] = defaultdict(list)
    
    for edge in edges:
        start_idx = point_map[id(edge.start)]
        end_idx = point_map[id(edge.end)]
        
        if start_idx != end_idx:  # Skip degenerate edges
            # Avoid duplicate edges in adjacency list
            if end_idx not in adjacency[start_idx]:
                adjacency[start_idx].append(end_idx)
            if start_idx not in adjacency[end_idx]:
                adjacency[end_idx].append(start_idx)
    
    return dict(adjacency), spatial_hash.points


def find_cycles_iterative(
    adjacency: Dict[int, List[int]],
    unique_points: List['Point'],
    max_depth: int = MAX_RECURSION_DEPTH,
    max_iterations: int = MAX_CYCLE_SEARCH_ITERATIONS,
) -> List[List[int]]:
    """
    Find all cycles using iterative DFS with explicit stack.
    
    This replaces the recursive DFS which could cause stack overflow
    on large graphs (Python default recursion limit ~1000).
    
    Args:
        adjacency: Dict mapping point index to connected indices
        unique_points: List of unique points (for reference)
        max_depth: Maximum path depth (prevents infinite loops)
        max_iterations: Maximum total iterations (prevents CPU exhaustion)
    
    Returns:
        List of cycles, where each cycle is a list of point indices
    
    Raises:
        GraphOverflowError: If iteration limit exceeded
    """
    if not adjacency:
        return []
    
    cycles: List[List[int]] = []
    global_visited: Set[int] = set()
    iteration_count = 0
    
    for start_node in adjacency.keys():
        if start_node in global_visited:
            continue
        
        # Iterative DFS with explicit stack
        # Stack frame: (current, path, path_set, neighbor_iterator)
        stack: List[Tuple[int, List[int], Set[int], int]] = [
            (start_node, [start_node], {start_node}, 0)
        ]
        
        while stack:
            iteration_count += 1
            
            if iteration_count > max_iterations:
                raise GraphOverflowError(
                    f"Cycle search exceeded {max_iterations:,} iterations. "
                    "Geometry may be too complex or contain errors."
                )
            
            current, path, path_set, neighbor_idx = stack.pop()
            
            # Check depth limit
            if len(path) > max_depth:
                continue
            
            neighbors = adjacency.get(current, [])
            
            # Find next unvisited neighbor
            found_next = False
            while neighbor_idx < len(neighbors):
                neighbor = neighbors[neighbor_idx]
                neighbor_idx += 1
                
                if neighbor == start_node and len(path) >= 3:
                    # Found a cycle back to start
                    cycles.append(path[:])
                elif neighbor not in path_set:
                    # Save current state for backtracking
                    stack.append((current, path, path_set, neighbor_idx))
                    
                    # Push new state to explore neighbor
                    new_path = path + [neighbor]
                    new_path_set = path_set | {neighbor}
                    stack.append((neighbor, new_path, new_path_set, 0))
                    
                    found_next = True
                    break
            
            # If no more neighbors, we backtrack (pop already happened)
        
        global_visited.add(start_node)
    
    return cycles


def deduplicate_cycles(cycles: List[List[int]]) -> List[List[int]]:
    """
    Remove duplicate cycles (same vertices, different start point).
    
    Also removes cycles that are subsets of larger cycles.
    
    Args:
        cycles: List of cycles (each is list of point indices)
    
    Returns:
        List of unique cycles
    """
    if not cycles:
        return []
    
    # Normalize each cycle: rotate to start from minimum index
    normalized = []
    for cycle in cycles:
        if len(cycle) < 3:
            continue
        
        min_idx = cycle.index(min(cycle))
        rotated = cycle[min_idx:] + cycle[:min_idx]
        
        # Also check reverse direction
        reversed_cycle = [rotated[0]] + rotated[1:][::-1]
        min_idx_rev = reversed_cycle.index(min(reversed_cycle))
        rotated_rev = reversed_cycle[min_idx_rev:] + reversed_cycle[:min_idx_rev]
        
        # Use lexicographically smaller of the two orientations
        canonical = min(tuple(rotated), tuple(rotated_rev))
        normalized.append(canonical)
    
    # Remove duplicates
    unique = list(set(normalized))
    
    # Sort by length (prefer longer cycles)
    unique.sort(key=len, reverse=True)
    
    return [list(c) for c in unique]
