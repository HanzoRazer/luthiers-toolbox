"""
Inlay Geometry BOM & Materials

Bill of Materials calculation, material definitions, and region clip shapes
for composing inlay patterns.

All coordinates in mm.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from .inlay_geometry_core import GeometryCollection, Polyline, Pt


# ---------------------------------------------------------------------------
# Material definitions
# ---------------------------------------------------------------------------

MATERIALS = {
    "mop":       {"name": "MOP White",      "color": "#ddeef8", "grain": "#c0d0dc"},
    "abalone":   {"name": "Abalone",        "color": "#58a87a", "grain": "#3a7858"},
    "black_mop": {"name": "Black MOP",      "color": "#28283a", "grain": "#181828"},
    "gold_mop":  {"name": "Gold MOP",       "color": "#d4a030", "grain": "#a87818"},
    "paua":      {"name": "Paua Abalone",   "color": "#3858a0", "grain": "#283878"},
    "ebony":     {"name": "Ebony",          "color": "#181008", "grain": "#0c0804"},
    "maple":     {"name": "Maple",          "color": "#eee0b0", "grain": "#d4c080"},
    "rosewood":  {"name": "Rosewood",       "color": "#481c10", "grain": "#341008"},
    "koa":       {"name": "Koa",            "color": "#c07020", "grain": "#a05010"},
    "bloodwood": {"name": "Bloodwood",      "color": "#981e10", "grain": "#781208"},
    "holly":     {"name": "Holly",          "color": "#f0f0e0", "grain": "#dcdcc8"},
    "walnut":    {"name": "Walnut",         "color": "#6a3c18", "grain": "#4a2810"},
    "bone":      {"name": "Bone",           "color": "#f0e8d0", "grain": "#e0d8c0"},
    "cedar":     {"name": "Cedar",          "color": "#c07040", "grain": "#a06030"},
}

MATERIAL_KEYS = list(MATERIALS.keys())


def mat_color(key: str) -> str:
    """Get the fill color for a material key."""
    return MATERIALS.get(key, {}).get("color", "#888888")


def mat_grain(key: str) -> str:
    """Get the grain color for a material key."""
    return MATERIALS.get(key, {}).get("grain", "#666666")


def mat_name(key: str) -> str:
    """Get the display name for a material key."""
    return MATERIALS.get(key, {}).get("name", key.title())


# ---------------------------------------------------------------------------
# BOM calculation
# ---------------------------------------------------------------------------

@dataclass
class BomEntry:
    """One row in a Bill of Materials for an inlay pattern."""
    shape_type: str
    material_key: str
    count: int
    area_mm2: float


def _shoelace_area(pts: List[Pt]) -> float:
    """Signed area of a simple polygon via the shoelace formula."""
    n = len(pts)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return abs(area) / 2.0


def calculate_bom(
    collection: GeometryCollection,
    materials: List[str] | None = None,
) -> List[BomEntry]:
    """Calculate a Bill of Materials from a GeometryCollection.

    Groups elements by (kind, material_key) and computes total count and
    area in mm² using the shoelace formula for polygons.
    """
    materials = materials or MATERIAL_KEYS[:3]
    buckets: dict[tuple[str, str], dict] = {}

    for el in collection.elements:
        mat_key = materials[el.material_index % len(materials)] if materials else "unknown"
        key = (el.kind, mat_key)
        if key not in buckets:
            buckets[key] = {"count": 0, "area": 0.0}
        buckets[key]["count"] += 1

        if el.kind == "polygon" and len(el.points) >= 3:
            buckets[key]["area"] += _shoelace_area(el.points)
        elif el.kind == "rect" and len(el.points) == 2:
            w = abs(el.points[1][0] - el.points[0][0])
            h = abs(el.points[1][1] - el.points[0][1])
            buckets[key]["area"] += w * h
        elif el.kind == "circle":
            buckets[key]["area"] += math.pi * el.radius ** 2

    return [
        BomEntry(shape_type=k[0], material_key=k[1], count=v["count"], area_mm2=round(v["area"], 2))
        for k, v in sorted(buckets.items())
    ]


# ---------------------------------------------------------------------------
# Region clip shapes — for the compose engine
# ---------------------------------------------------------------------------

def fretboard_trapezoid(
    nut_width_mm: float,
    body_width_mm: float,
    length_mm: float,
) -> List[Pt]:
    """A tapered fretboard trapezoid — narrow at nut (top), wider at body (bottom).

    Centred horizontally; nut edge at y=0, body edge at y=length_mm.
    """
    half_nut = nut_width_mm / 2
    half_body = body_width_mm / 2
    return [
        (-half_nut, 0),
        (half_nut, 0),
        (half_body, length_mm),
        (-half_body, length_mm),
    ]


def rosette_ring(
    outer_r: float,
    inner_r: float,
    n_segments: int = 64,
) -> Tuple[List[Pt], List[Pt]]:
    """Concentric annular ring as two polyline circles.

    Returns (outer_ring, inner_ring) — both are closed polylines.
    """
    def _circle(r: float) -> List[Pt]:
        return [
            (r * math.cos(i * 2 * math.pi / n_segments),
             r * math.sin(i * 2 * math.pi / n_segments))
            for i in range(n_segments)
        ]
    return (_circle(outer_r), _circle(inner_r))


def binding_strip(
    length_mm: float,
    width_mm: float,
) -> List[Pt]:
    """Simple rectangular binding strip region.

    Anchored at origin; extends along X for length, Y for width.
    """
    return [
        (0, 0),
        (length_mm, 0),
        (length_mm, width_mm),
        (0, width_mm),
    ]
