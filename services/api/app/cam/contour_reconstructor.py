"""================================================================================"""

import math
from typing import List, Tuple, Optional, Dict, Any, Set
from collections import defaultdict
import ezdxf
from pydantic import BaseModel


# =============================================================================
# DATA STRUCTURES (POINT, EDGE, LOOP MODELS)
# =============================================================================

class Point:
    """2D point with tolerance-based equality"""
    def __init__(self, x: float, y: float, tolerance: float = 0.1):
        self.x = x
        self.y = y
        self.tolerance = tolerance
    
    def distance_to(self, other: 'Point') -> float:
        """Euclidean distance to another point"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx*dx + dy*dy)
    
    def is_close(self, other: 'Point', tolerance: float = None) -> bool:
        """Check if points are within tolerance"""
        tol = tolerance if tolerance is not None else self.tolerance
        return self.distance_to(other) < tol
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (x, y) tuple"""
        return (self.x, self.y)
    
    def __repr__(self):
        return f"Point({self.x:.2f}, {self.y:.2f})"


class Edge:
    """Directed edge (line segment) in connectivity graph"""
    def __init__(self, start: Point, end: Point, entity_type: str, entity_data: Any = None):
        self.start = start
        self.end = end
        self.entity_type = entity_type  # 'LINE' or 'SPLINE'
        self.entity_data = entity_data  # Original ezdxf entity
    
    def __repr__(self):
        return f"Edge({self.start} -> {self.end}, {self.entity_type})"


class Loop(BaseModel):
    """Closed polygon loop (matches adaptive_router.py format)"""
    pts: List[Tuple[float, float]]
    
    class Config:
        arbitrary_types_allowed = True


class ReconstructionResult(BaseModel):
    """Result of contour reconstruction"""
    loops: List[Loop]
    outer_loop_idx: int = 0  # Index of outer boundary (largest area)
    warnings: List[str] = []
    stats: Dict[str, Any] = {}


# =============================================================================
# SPLINE ADAPTIVE SAMPLING
# =============================================================================

def sample_spline(spline_entity, max_segments: int = 50, max_error_mm: float = 0.1) -> List[Tuple[float, float]]:
    """Adaptively sample a SPLINE entity to polyline points."""
    try:
        # Use ezdxf's built-in flattening (returns Vec3 objects)
        # distance parameter controls sampling density (smaller = more points)
        points_3d = list(spline_entity.flattening(distance=max_error_mm))
        
        # Convert Vec3 to (x, y) tuples
        points = [(p.x, p.y) for p in points_3d]
        
        # Limit segments if too many
        if len(points) > max_segments:
            # Downsample by taking every Nth point
            step = len(points) // max_segments
            points = points[::step]
            # Always include last point
            if points[-1] != points_3d[-1]:
                points.append((points_3d[-1].x, points_3d[-1].y))
        
        return points
    
    except (AttributeError, RuntimeError, TypeError, ValueError) as e:
        # Fallback: Linear sampling with fixed segments
        points = []
        for i in range(max_segments + 1):
            t = i / max_segments
            try:
                p = spline_entity.point(t)
                points.append((p.x, p.y))
            except (AttributeError, RuntimeError):
                pass
        return points if points else [(0, 0), (1, 1)]  # Dummy fallback


# =============================================================================
# EDGE GRAPH CONSTRUCTION
# =============================================================================

def build_edge_graph(lines: List, splines: List, tolerance: float = 0.1) -> List[Edge]:
    """Build list of directed edges from LINE and SPLINE entities."""
    edges = []
    
    # Process LINEs
    for line in lines:
        start = Point(line.dxf.start.x, line.dxf.start.y, tolerance)
        end = Point(line.dxf.end.x, line.dxf.end.y, tolerance)
        edges.append(Edge(start, end, 'LINE', line))
    
    # Process SPLINEs (sample to polyline segments)
    for spline in splines:
        points = sample_spline(spline, max_segments=30, max_error_mm=0.1)
        
        # Create edges between consecutive sampled points
        for i in range(len(points) - 1):
            start = Point(points[i][0], points[i][1], tolerance)
            end = Point(points[i+1][0], points[i+1][1], tolerance)
            edges.append(Edge(start, end, 'SPLINE', spline))
    
    return edges


# =============================================================================
# ADJACENCY MAP & POINT DEDUPLICATION
# =============================================================================

def build_adjacency_map(edges: List[Edge]) -> Dict[int, List[int]]:
    """
    Build adjacency map for graph traversal.
    
    Uses point hashing with tolerance to match endpoints.
    
    Returns:
        Dict mapping point_idx -> [connected_point_indices]
    """
    # Deduplicate points (merge within tolerance)
    unique_points = []
    point_map = {}  # Maps original point to unique point index
    
    for edge in edges:
        # Check if start point exists
        start_idx = None
        for i, p in enumerate(unique_points):
            if edge.start.is_close(p):
                start_idx = i
                break
        if start_idx is None:
            start_idx = len(unique_points)
            unique_points.append(edge.start)
        
        # Check if end point exists
        end_idx = None
        for i, p in enumerate(unique_points):
            if edge.end.is_close(p):
                end_idx = i
                break
        if end_idx is None:
            end_idx = len(unique_points)
            unique_points.append(edge.end)
        
        # Store mapping
        point_map[id(edge.start)] = start_idx
        point_map[id(edge.end)] = end_idx
    
    # Build adjacency list
    adjacency = defaultdict(list)
    for edge in edges:
        start_idx = point_map.get(id(edge.start))
        end_idx = point_map.get(id(edge.end))
        if start_idx is not None and end_idx is not None:
            adjacency[start_idx].append(end_idx)
            # Add reverse edge for undirected graph traversal
            adjacency[end_idx].append(start_idx)
    
    return adjacency, unique_points


# =============================================================================
# CYCLE DETECTION (DEPTH-FIRST SEARCH)
# =============================================================================

def find_cycles_dfs(adjacency: Dict[int, List[int]], unique_points: List[Point]) -> List[List[int]]:
    """
    Find all cycles in the graph using depth-first search.
    
    Returns:
        List of cycles, where each cycle is a list of point indices
    """
    cycles = []
    visited = set()
    
    def dfs(start: int, current: int, path: List[int], path_set: Set[int]):
        """Recursive DFS to find cycles"""
        if current in path_set:
            # Found a cycle
            if current == start and len(path) >= 3:
                cycles.append(path[:])
            return
        
        if current in visited:
            return
        
        path.append(current)
        path_set.add(current)
        
        # Explore neighbors
        for neighbor in adjacency.get(current, []):
            if neighbor == start and len(path) >= 3:
                # Completed cycle back to start
                cycles.append(path[:])
            elif neighbor not in path_set:
                dfs(start, neighbor, path, path_set)
        
        path.pop()
        path_set.remove(current)
    
    # Try starting DFS from each node
    for start_node in adjacency.keys():
        if start_node not in visited:
            dfs(start_node, start_node, [], set())
            visited.add(start_node)
    
    return cycles


def deduplicate_cycles(cycles: List[List[int]]) -> List[List[int]]:
    """
    Remove duplicate cycles (same vertices, different start point).
    """
    unique_cycles = []
    seen_sets = []
    
    for cycle in cycles:
        # Normalize cycle (start from minimum index)
        min_idx = cycle.index(min(cycle))
        normalized = cycle[min_idx:] + cycle[:min_idx]
        
        # Check if we've seen this cycle
        cycle_set = frozenset(cycle)
        if cycle_set not in seen_sets:
            unique_cycles.append(normalized)
            seen_sets.append(cycle_set)
    
    return unique_cycles


# =============================================================================
# LOOP CLASSIFICATION (WINDING ORDER DETECTION)
# =============================================================================

def compute_polygon_area(points: List[Point]) -> float:
    """
    Compute signed area of polygon using shoelace formula.
    Positive area = counter-clockwise winding.
    """
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
    return area / 2.0


def classify_loops(cycles: List[List[int]], unique_points: List[Point]) -> Tuple[int, List[int]]:
    """
    Classify loops as outer boundary or islands (holes).
    
    Returns:
        (outer_loop_idx, island_indices)
    """
    if not cycles:
        return -1, []
    
    # Compute area for each cycle
    areas = []
    for cycle in cycles:
        pts = [unique_points[i] for i in cycle]
        area = abs(compute_polygon_area(pts))
        areas.append(area)
    
    # Largest area = outer boundary
    outer_idx = areas.index(max(areas))
    
    # Rest are islands (if any)
    island_indices = [i for i in range(len(cycles)) if i != outer_idx]
    
    return outer_idx, island_indices


# =============================================================================
# MAIN RECONSTRUCTION PIPELINE
# =============================================================================

def reconstruct_contours_from_dxf(
    dxf_bytes: bytes,
    layer_name: str = "Contours",
    tolerance: float = 0.1,
    min_loop_points: int = 3
) -> ReconstructionResult:
    """Reconstruct closed contours from DXF primitives (LINE + SPLINE)."""
    warnings = []
    
    # Load DXF
    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf', mode='wb') as tmp:
            tmp.write(dxf_bytes)
            tmp_path = tmp.name
        
        try:
            doc = ezdxf.readfile(tmp_path)
            msp = doc.modelspace()
        finally:
            os.unlink(tmp_path)
    except (IOError, OSError, ValueError) as e:
        warnings.append(f"Failed to read DXF: {e}")
        return ReconstructionResult(loops=[], warnings=warnings)
    
    # Extract LINEs and SPLINEs from specified layer
    all_entities = list(msp)
    lines = [e for e in all_entities if e.dxftype() == 'LINE' and e.dxf.layer == layer_name]
    splines = [e for e in all_entities if e.dxftype() == 'SPLINE' and e.dxf.layer == layer_name]
    
    if not lines and not splines:
        # Try fallback to all layers
        lines = [e for e in all_entities if e.dxftype() == 'LINE']
        splines = [e for e in all_entities if e.dxftype() == 'SPLINE']
        if lines or splines:
            warnings.append(f"No geometry on layer '{layer_name}', using all layers")
        else:
            warnings.append(f"No LINE or SPLINE entities found in DXF")
            return ReconstructionResult(loops=[], warnings=warnings)
    
    # Build edge graph
    edges = build_edge_graph(lines, splines, tolerance)
    if not edges:
        warnings.append("No edges built from geometry")
        return ReconstructionResult(loops=[], warnings=warnings)
    
    # Security patch: Use safe algorithms with O(n) spatial hash and iterative DFS
    from app.cam.graph_algorithms import (
        build_adjacency_map_safe,
        find_cycles_iterative,
        deduplicate_cycles,
        GraphOverflowError,
    )
    
    # Build adjacency map with spatial hash (O(n) vs O(n²))
    try:
        adjacency, unique_points = build_adjacency_map_safe(edges, tolerance=tolerance)
    except GraphOverflowError as e:
        warnings.append(f"Graph construction failed: {str(e)}")
        return ReconstructionResult(loops=[], warnings=warnings)
    
    # Find cycles with iterative DFS (prevents stack overflow)
    try:
        cycles = find_cycles_iterative(adjacency, unique_points)
    except GraphOverflowError as e:
        warnings.append(f"Cycle detection failed: {str(e)}")
        return ReconstructionResult(loops=[], warnings=warnings)
    
    if not cycles:
        warnings.append(f"No closed cycles found. Check geometry connectivity (tolerance={tolerance}mm)")
        return ReconstructionResult(loops=[], warnings=warnings)
    
    # Deduplicate
    cycles = deduplicate_cycles(cycles)
    
    # Classify loops
    outer_idx, island_indices = classify_loops(cycles, unique_points)
    
    # Convert to Loop format
    loops = []
    for cycle in cycles:
        pts = [unique_points[i].to_tuple() for i in cycle]
        if len(pts) >= min_loop_points:
            loops.append(Loop(pts=pts))
    
    # Stats
    stats = {
        "lines_found": len(lines),
        "splines_found": len(splines),
        "edges_built": len(edges),
        "unique_points": len(unique_points),
        "cycles_found": len(cycles),
        "loops_extracted": len(loops)
    }
    
    return ReconstructionResult(
        loops=loops,
        outer_loop_idx=outer_idx if outer_idx >= 0 else 0,
        warnings=warnings,
        stats=stats
    )
