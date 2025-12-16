"""
Triangle mesh model for CAM geometry.

Supports metadata for debug + golden snapshot context.

Target: instrument_geometry/models/mesh.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

Vec3 = Tuple[float, float, float]
Tri = Tuple[int, int, int]


@dataclass
class TriangleMesh:
    vertices: List[Vec3]
    triangles: List[Tri]
    # Optional metadata for debug + golden snapshot context
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_json(self):
        out = {
            "type": "triangle_mesh",
            "vertex_count": len(self.vertices),
            "triangle_count": len(self.triangles),
            "vertices": [{"x": v[0], "y": v[1], "z": v[2]} for v in self.vertices],
            "triangles": [{"a": t[0], "b": t[1], "c": t[2]} for t in self.triangles],
        }
        if self.meta:
            out["meta"] = self.meta
        return out
