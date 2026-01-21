"""
Unit tests for mesh/o3d_heal.py

Tests the topology computation functions independent of Open3D availability.
"""
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.mesh.o3d_heal import (
    _edge_map_from_triangles,
    _boundary_loops,
    _edge_lengths,
    _parse_obj,
    heal_mesh,
    HealReport,
)


class TestEdgeMapFromTriangles:
    """Test edge counting from triangle faces."""

    def test_single_triangle(self):
        """Single triangle has 3 edges, each with count 1."""
        F = np.array([[0, 1, 2]], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        assert len(edge_map) == 3
        assert all(c == 1 for c in edge_map.values())

    def test_two_adjacent_triangles(self):
        """Two triangles sharing an edge: shared edge has count 2, others have 1."""
        # Triangle 0-1-2 and 1-2-3 share edge 1-2
        F = np.array([
            [0, 1, 2],
            [1, 3, 2]
        ], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        # Edge (1,2) should have count 2
        shared_edge = (1, 2)
        assert edge_map[shared_edge] == 2
        # Other edges have count 1
        boundary_edges = [(k, v) for k, v in edge_map.items() if k != shared_edge]
        assert all(c == 1 for _, c in boundary_edges)

    def test_closed_tetrahedron(self):
        """Closed tetrahedron: 4 faces, 6 edges, each edge has count 2 (manifold)."""
        F = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
            [1, 3, 2]
        ], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        assert len(edge_map) == 6
        # All edges should have exactly 2 adjacent faces (watertight)
        assert all(c == 2 for c in edge_map.values())

    def test_empty_faces(self):
        """Empty face array returns empty edge map."""
        F = np.zeros((0, 3), dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        assert len(edge_map) == 0


class TestBoundaryLoops:
    """Test hole counting via connected components of boundary edges."""

    def test_single_triangle_one_loop(self):
        """Single triangle has 1 boundary loop (the triangle edge)."""
        F = np.array([[0, 1, 2]], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        loops = _boundary_loops(edge_map)
        assert loops == 1

    def test_closed_tetrahedron_no_holes(self):
        """Closed tetrahedron has no boundary edges → 0 holes."""
        F = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
            [1, 3, 2]
        ], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        loops = _boundary_loops(edge_map)
        assert loops == 0

    def test_two_disconnected_triangles_two_loops(self):
        """Two disconnected triangles have 2 boundary loops."""
        F = np.array([
            [0, 1, 2],
            [3, 4, 5]
        ], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        loops = _boundary_loops(edge_map)
        assert loops == 2


class TestEdgeLengths:
    """Test edge length statistics."""

    def test_unit_triangle(self):
        """Unit triangle: edges of length 1."""
        V = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, np.sqrt(3)/2, 0.0]
        ])
        F = np.array([[0, 1, 2]], dtype=np.int64)
        mean_len, std_len = _edge_lengths(V, F)
        # Equilateral triangle with side ~1
        assert pytest.approx(mean_len, rel=0.01) == 1.0
        assert std_len < 0.01  # Nearly zero std for equilateral

    def test_empty_mesh(self):
        """Empty mesh returns (0, 0)."""
        V = np.zeros((0, 3))
        F = np.zeros((0, 3), dtype=np.int64)
        mean_len, std_len = _edge_lengths(V, F)
        assert mean_len == 0.0
        assert std_len == 0.0


class TestParseObj:
    """Test OBJ parsing."""

    def test_simple_triangle(self):
        """Parse a simple triangle OBJ."""
        obj_content = """
# Simple triangle
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.5 1.0 0.0
f 1 2 3
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.obj', delete=False) as f:
            f.write(obj_content)
            f.flush()
            V, F = _parse_obj(Path(f.name))
        
        assert V.shape == (3, 3)
        assert F.shape == (1, 3)
        # Check face indices are 0-based
        assert list(F[0]) == [0, 1, 2]

    def test_obj_with_texture_coords(self):
        """Parse OBJ with v/vt/vn format."""
        obj_content = """
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.5 1.0 0.0
vt 0.0 0.0
vt 1.0 0.0
vt 0.5 1.0
f 1/1 2/2 3/3
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.obj', delete=False) as f:
            f.write(obj_content)
            f.flush()
            V, F = _parse_obj(Path(f.name))
        
        assert V.shape == (3, 3)
        assert F.shape == (1, 3)
        assert list(F[0]) == [0, 1, 2]


class TestHealMesh:
    """Test the heal_mesh function end-to-end."""

    def test_heal_simple_obj(self):
        """Heal a simple triangle OBJ (fallback path if no Open3D)."""
        obj_content = """# Simple triangle
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.5 0.866 0.0
f 1 2 3
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "input.obj"
            dst = Path(tmpdir) / "healed.obj"
            src.write_text(obj_content)
            
            report = heal_mesh(src, dst)
            
            assert isinstance(report, HealReport)
            assert report.vertices == 3
            assert report.faces == 1
            assert report.holes == 1  # Single triangle has 1 boundary loop
            assert report.nonmanifold_edges == 0
            assert dst.exists()

    def test_heal_creates_output_dir(self):
        """heal_mesh creates parent directories if needed."""
        obj_content = "v 0 0 0\nv 1 0 0\nv 0.5 1 0\nf 1 2 3\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "input.obj"
            dst = Path(tmpdir) / "subdir" / "nested" / "healed.obj"
            src.write_text(obj_content)
            
            report = heal_mesh(src, dst)
            
            assert dst.exists()
            assert report.out_mesh_path == str(dst)


class TestNonManifoldDetection:
    """Test non-manifold edge detection."""

    def test_three_triangles_sharing_edge_nonmanifold(self):
        """Three triangles sharing the same edge creates non-manifold geometry."""
        # Triangles 0-1-2, 0-1-3, 0-1-4 all share edge 0-1
        F = np.array([
            [0, 1, 2],
            [0, 1, 3],
            [0, 1, 4]
        ], dtype=np.int64)
        edge_map = _edge_map_from_triangles(F)
        # Edge (0,1) has count 3 → non-manifold
        nonman_count = sum(1 for c in edge_map.values() if c > 2)
        assert nonman_count == 1
        assert edge_map[(0, 1)] == 3
