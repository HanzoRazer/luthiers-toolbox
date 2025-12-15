# services/api/app/cam/spatial_hash.py
"""
Spatial Hash for O(n) Point Deduplication

Replaces O(n²) linear scan with O(1) average hash lookup.

The Problem:
    Original code scanned all existing points for each new point:
    
        for edge in edges:                    # O(n) edges
            for p in unique_points:           # O(n) points
                if edge.start.is_close(p):   # O(n²) total!
    
    With 5,000 points: 25 million comparisons
    With 50,000 points: 2.5 billion comparisons

The Solution:
    Hash points into grid cells. Only compare within neighboring cells:
    
        for edge in edges:                    # O(n) edges
            cell = hash(edge.start)           # O(1)
            for p in cells[cell]:             # O(~10) neighbors
                ...                           # O(n) total!

Usage:
    from app.cam.spatial_hash import SpatialHash
    
    hasher = SpatialHash(cell_size=0.1)
    
    for point in points:
        idx = hasher.get_or_add(point, tolerance=0.001)
        # idx is unique index, reused for duplicate points
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Protocol, TYPE_CHECKING

from app.cam.dxf_limits import SPATIAL_HASH_CELL_SIZE_MM, MAX_DXF_POINTS


class PointLike(Protocol):
    """Protocol for point-like objects with x, y coordinates."""
    x: float
    y: float
    
    def is_close(self, other: 'PointLike', tolerance: float = 0.001) -> bool:
        """Check if this point is within tolerance of another."""
        ...


class SpatialHash:
    """
    2D spatial hash for efficient point deduplication.
    
    Divides the plane into grid cells and hashes points by cell.
    Point lookups only check the 3x3 neighborhood of cells,
    giving O(1) average case instead of O(n).
    
    Attributes:
        cell_size: Grid cell size in mm (default 0.1mm)
        points: List of unique points (in insertion order)
        cells: Dict mapping (cell_x, cell_y) to list of (index, point)
    
    Example:
        hasher = SpatialHash()
        
        # Add points, getting unique indices
        idx1 = hasher.get_or_add(Point(0, 0))      # Returns 0
        idx2 = hasher.get_or_add(Point(0.0001, 0)) # Returns 0 (same point)
        idx3 = hasher.get_or_add(Point(10, 10))    # Returns 1 (new point)
        
        # Get all unique points
        unique = hasher.points  # [Point(0,0), Point(10,10)]
    """
    
    def __init__(self, cell_size: float = SPATIAL_HASH_CELL_SIZE_MM):
        """
        Initialize spatial hash.
        
        Args:
            cell_size: Grid cell size in mm. Smaller = more precise
                       but more memory. 0.1mm is good for CNC tolerance.
        """
        if cell_size <= 0:
            raise ValueError(f"cell_size must be positive, got {cell_size}")
        
        self.cell_size = cell_size
        self.points: List[PointLike] = []
        self.cells: Dict[Tuple[int, int], List[Tuple[int, PointLike]]] = defaultdict(list)
    
    def _cell_key(self, x: float, y: float) -> Tuple[int, int]:
        """
        Get cell coordinates for a point.
        
        Uses floor division to map coordinates to cell indices.
        """
        return (int(x // self.cell_size), int(y // self.cell_size))
    
    def add_point(self, point: PointLike) -> int:
        """
        Add point unconditionally and return its index.
        
        Does NOT check for duplicates. Use get_or_add() for deduplication.
        
        Args:
            point: Point to add
        
        Returns:
            Index of the newly added point
        
        Raises:
            ValueError: If point count exceeds MAX_DXF_POINTS
        """
        if len(self.points) >= MAX_DXF_POINTS:
            raise ValueError(
                f"Point count exceeds limit ({MAX_DXF_POINTS}). "
                "Simplify the DXF geometry."
            )
        
        idx = len(self.points)
        self.points.append(point)
        
        key = self._cell_key(point.x, point.y)
        self.cells[key].append((idx, point))
        
        return idx
    
    def find_existing(
        self,
        point: PointLike,
        tolerance: float = 0.001
    ) -> Optional[int]:
        """
        Find existing point within tolerance.
        
        Checks the point's cell and all 8 neighboring cells to handle
        points near cell boundaries.
        
        Args:
            point: Point to search for
            tolerance: Distance tolerance for matching (default 0.001mm)
        
        Returns:
            Index of matching point if found, None otherwise
        """
        cx, cy = self._cell_key(point.x, point.y)
        
        # Check 3x3 neighborhood of cells
        # This handles points near cell boundaries
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                key = (cx + dx, cy + dy)
                cell_points = self.cells.get(key)
                
                if cell_points:
                    for idx, existing in cell_points:
                        if point.is_close(existing, tolerance):
                            return idx
        
        return None
    
    def get_or_add(
        self,
        point: PointLike,
        tolerance: float = 0.001
    ) -> int:
        """
        Find existing point or add new one.
        
        This is the main deduplication method. It first searches for
        a matching point within tolerance. If found, returns the existing
        index. If not found, adds the point and returns its new index.
        
        Args:
            point: Point to find or add
            tolerance: Distance tolerance for matching
        
        Returns:
            Index of the point (existing or newly added)
        """
        existing = self.find_existing(point, tolerance)
        if existing is not None:
            return existing
        return self.add_point(point)
    
    def __len__(self) -> int:
        """Return number of unique points."""
        return len(self.points)
    
    def clear(self) -> None:
        """Clear all points and cells."""
        self.points.clear()
        self.cells.clear()
