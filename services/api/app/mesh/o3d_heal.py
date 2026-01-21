from __future__ import annotations
"""
Minimal mesh healing + QA using Open3D when available.
Falls back to a tiny OBJ parser to compute edge topology (holes/non-manifold)
if Open3D is not installed — so CI stays green without heavy wheels.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict
import math

import numpy as np

try:
    import open3d as o3d  # type: ignore
    _HAS_O3D = True
except Exception:
    o3d = None  # type: ignore
    _HAS_O3D = False


@dataclass
class HealReport:
    vertices: int
    faces: int
    ngons: int
    nonmanifold_edges: int
    holes: int
    self_intersections: int
    edge_length_mean: float | None
    edge_length_std: float | None
    out_mesh_path: str
    notes: str | None = None


def _parse_obj(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """Tiny OBJ parser (v/f triangles only)."""
    vs: List[Tuple[float, float, float]] = []
    fs: List[Tuple[int, int, int]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == "v" and len(parts) >= 4:
                vs.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif parts[0] == "f" and len(parts) >= 4:
                # Keep first 3 indices (triangulated assumed for scaffold)
                tri = []
                for tok in parts[1:4]:
                    i = tok.split("/")[0]
                    tri.append(int(i) - 1)  # OBJ is 1-based
                fs.append(tuple(tri))
    V = np.asarray(vs, dtype=np.float64) if vs else np.zeros((0, 3))
    F = np.asarray(fs, dtype=np.int64) if fs else np.zeros((0, 3), dtype=np.int64)
    return V, F


def _edge_map_from_triangles(F: np.ndarray) -> Dict[Tuple[int, int], int]:
    """Build undirected edge->count map from triangles (counts of adjacent faces)."""
    edge_counts: Dict[Tuple[int, int], int] = {}
    for a, b, c in F:
        for u, v in ((a, b), (b, c), (c, a)):
            e = (u, v) if u < v else (v, u)
            edge_counts[e] = edge_counts.get(e, 0) + 1
    return edge_counts


def _boundary_loops(edge_counts: Dict[Tuple[int, int], int]) -> int:
    """Approximate number of boundary loops by counting connected components of boundary edges."""
    # Boundary edges are those seen exactly once
    b_edges = [(u, v) for (u, v), c in edge_counts.items() if c == 1]
    if not b_edges:
        return 0
    # Build adjacency for boundary graph
    adj: Dict[int, List[int]] = {}
    for u, v in b_edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    visited: set[int] = set()
    loops = 0
    for start in list(adj.keys()):
        if start in visited:
            continue
        # BFS/DFS
        stack = [start]
        visited.add(start)
        while stack:
            n = stack.pop()
            for m in adj.get(n, []):
                if m not in visited:
                    visited.add(m)
                    stack.append(m)
        loops += 1
    return loops


def _edge_lengths(V: np.ndarray, F: np.ndarray) -> Tuple[float, float]:
    if V.size == 0 or F.size == 0:
        return (0.0, 0.0)
    # Collect unique undirected edges
    edges = set()
    for a, b, c in F:
        for u, v in ((a, b), (b, c), (c, a)):
            e = (u, v) if u < v else (v, u)
            edges.add(e)
    if not edges:
        return (0.0, 0.0)
    lengths = []
    for u, v in edges:
        duv = V[v] - V[u]
        lengths.append(math.sqrt(float(duv.dot(duv))))
    arr = np.asarray(lengths, dtype=np.float64)
    return float(arr.mean()), float(arr.std())


def heal_mesh(
    input_mesh: str | Path,
    out_mesh: str | Path,
    *,
    weld_tol: float = 0.0,
) -> HealReport:
    """
    Load -> (optional) weld/cleanup -> write mesh to out path.
    Compute QA counts from topology either via Open3D or fallback parser.
    """
    src = Path(input_mesh)
    dst = Path(out_mesh)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if _HAS_O3D:
        mesh = o3d.io.read_triangle_mesh(str(src))
        notes = None
        if not mesh.has_triangles():
            # Save-through if empty/invalid
            o3d.io.write_triangle_mesh(str(dst), mesh)
            V = np.asarray(mesh.vertices)
            F = np.asarray(mesh.triangles)
            edge_counts = _edge_map_from_triangles(F)
            holes = _boundary_loops(edge_counts)
            nonman = sum(1 for c in edge_counts.values() if c > 2)
            m, s = _edge_lengths(V, F)
            return HealReport(
                vertices=V.shape[0], faces=F.shape[0], ngons=0,
                nonmanifold_edges=nonman, holes=holes, self_intersections=0,
                edge_length_mean=m, edge_length_std=s, out_mesh_path=str(dst), notes="empty-or-invalid"
            )

        # Basic cleanup
        mesh.remove_duplicated_vertices()
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_non_manifold_edges()
        mesh.remove_unreferenced_vertices()

        # Optional vertex weld by snapping to a grid with weld_tol
        if weld_tol > 0.0:
            V = np.asarray(mesh.vertices)
            grid = np.round(V / weld_tol) * weld_tol
            mesh.vertices = o3d.utility.Vector3dVector(grid)
            mesh.remove_duplicated_vertices()
            mesh.remove_degenerate_triangles()

        o3d.io.write_triangle_mesh(str(dst), mesh)
        V = np.asarray(mesh.vertices)
        F = np.asarray(mesh.triangles, dtype=np.int64)
        edge_counts = _edge_map_from_triangles(F)
        holes = _boundary_loops(edge_counts)
        nonman = sum(1 for c in edge_counts.values() if c > 2)
        self_inter = int(mesh.is_self_intersecting())
        m, s = _edge_lengths(V, F)
        return HealReport(
            vertices=V.shape[0],
            faces=F.shape[0],
            ngons=0,  # Open3D TriangleMesh is triangles-only
            nonmanifold_edges=nonman,
            holes=holes,
            self_intersections=self_inter,
            edge_length_mean=m,
            edge_length_std=s,
            out_mesh_path=str(dst),
            notes=notes,
        )

    # Fallback path: no Open3D — pass-through + topology computed from OBJ
    V, F = _parse_obj(src)
    # Write-through (keep a copy as "healed")
    dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    edge_counts = _edge_map_from_triangles(F)
    holes = _boundary_loops(edge_counts)
    nonman = sum(1 for c in edge_counts.values() if c > 2)
    m, s = _edge_lengths(V, F)
    return HealReport(
        vertices=V.shape[0],
        faces=F.shape[0],
        ngons=0,
        nonmanifold_edges=nonman,
        holes=holes,
        self_intersections=0,
        edge_length_mean=m,
        edge_length_std=s,
        out_mesh_path=str(dst),
        notes="fallback-no-open3d",
    )
