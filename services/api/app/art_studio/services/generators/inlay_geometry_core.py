"""
Inlay Geometry Core Data Model

Defines GeometryElement and GeometryCollection - the intermediate representation
for all inlay pattern generators.

All coordinates in mm.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

# Type aliases for 2D geometry
Pt = Tuple[float, float]
Polyline = List[Pt]


@dataclass
class GeometryElement:
    """Single geometric primitive in mm coordinates."""

    kind: str  # "polygon", "polyline", "circle", "rect"
    points: List[Pt] = field(default_factory=list)
    # For circles: centre is points[0], radius stored separately
    radius: float = 0.0
    # For rects: (x, y, w, h) encoded in points as [(x,y), (x+w, y+h)]
    material_index: int = 0
    stroke_width: float = 0.25
    grain_angle: float = 0.0  # Wood grain direction in degrees


@dataclass
class GeometryCollection:
    """Complete output of one pattern generation call.

    Fields
    ------
    elements : list[GeometryElement]
        Raw pattern geometry (the *centerline*).
    width_mm, height_mm : float
        Bounding box of the *design* region.
    origin_x, origin_y : float
        Translation applied before rendering (for radial patterns centred at 0,0).
    radial : bool
        True for patterns that centre on the origin (spiral, sunburst, feather).
    tile_w, tile_h : float | None
        For linear-tiling patterns, the single-tile footprint.
    """

    elements: List[GeometryElement] = field(default_factory=list)
    width_mm: float = 0.0
    height_mm: float = 0.0
    origin_x: float = 0.0
    origin_y: float = 0.0
    radial: bool = False
    tile_w: float | None = None
    tile_h: float | None = None
