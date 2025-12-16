"""
OBJ mesh exporter for preview-ready output.

Target: instrument_geometry/exports/mesh_obj.py
"""
from __future__ import annotations

from pathlib import Path
from ..models.mesh import TriangleMesh


def export_obj(mesh: TriangleMesh, path: Path) -> Path:
    """
    Export a TriangleMesh to Wavefront OBJ format.
    
    Compatible with Blender, FreeCAD, Fusion 360, MeshLab.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# pocket sidewall mesh\n")
        for (x, y, z) in mesh.vertices:
            f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for (a, b, c) in mesh.triangles:
            # OBJ is 1-based
            f.write(f"f {a+1} {b+1} {c+1}\n")
    return path
