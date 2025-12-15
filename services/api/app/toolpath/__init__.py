# services/api/app/toolpath/__init__.py
"""
Toolpath engine package.

Wave 1:
- Basic vcarve toolpath builder (SVG → segments → G-code).
- Legacy DXF I/O adapter (to be wired behind versioned exporter).

The MLPath class is the core spine data structure for geometry:
- Used by Art Studio for SVG → toolpath conversions
- Used by DXF import/export
- Used by rosette and relief geometry generators
"""

from typing import List, Tuple

Point2D = Tuple[float, float]


class MLPath:
    """
    Minimal "M/L path" representation.

    This is the core geometry spine used across Art Studio and RMOS:
    - Rosette geometry → MLPaths → DXF
    - Relief geometry → MLPaths → DXF
    - SVG ingest → MLPaths → G-code
    - DXF import → MLPaths → canvas preview

    Attributes:
        points: List of (x, y) coordinate tuples
        is_closed: Whether the path forms a closed loop
    """

    def __init__(self, points: List[Point2D], is_closed: bool = False) -> None:
        self.points = points
        self.is_closed = is_closed

    def __repr__(self) -> str:
        return f"MLPath(len={len(self.points)}, closed={self.is_closed})"

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def copy(self) -> "MLPath":
        """Return a shallow copy of this MLPath."""
        return MLPath(points=list(self.points), is_closed=self.is_closed)


__all__ = ["MLPath", "Point2D"]
